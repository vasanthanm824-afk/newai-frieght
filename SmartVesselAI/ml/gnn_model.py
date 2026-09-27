"""Spatial Graph Neural Network (GNN) Regressor for Maritime Freight Forecasting.

Features:
- Construct spatial route similarity and port connectivity graph adjacency matrix
- Normalized Graph Convolutional Network (GCN) message passing layers
- Graph pooling and spatial readout regression heads
- Standard Scikit-Learn fit/predict interface compatible with ensemble models
- Supports PyTorch engine if available, with memory-efficient NumPy GCN fallback
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
from typing import Any

HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    pass


if HAS_TORCH:
    class PyTorchGCNLayer(nn.Module):
        """Graph Convolutional Layer (Kipf & Welling)."""
        def __init__(self, in_features: int, out_features: int):
            super().__init__()
            self.linear = nn.Linear(in_features, out_features)
            self.elu = nn.ELU()

        def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
            # x: (batch_size, in_features) or (nodes, in_features)
            support = self.linear(x)
            if adj_norm.dim() == 2 and x.dim() == 2:
                out = torch.mm(adj_norm, support)
            else:
                out = support
            return self.elu(out)

    class PyTorchGNNModule(nn.Module):
        """PyTorch Graph Neural Network module for spatial trade route regression."""
        def __init__(self, input_dim: int, hidden_dim: int = 64, dropout: float = 0.1):
            super().__init__()
            self.gcn1 = PyTorchGCNLayer(input_dim, hidden_dim)
            self.gcn2 = PyTorchGCNLayer(hidden_dim, hidden_dim)
            self.dropout = nn.Dropout(dropout)
            self.head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ELU(),
                nn.Linear(hidden_dim // 2, 1)
            )

        def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
            h = self.gcn1(x, adj_norm)
            h = self.dropout(h)
            h = self.gcn2(h, adj_norm)
            out = self.head(h)
            return out.squeeze(-1)


class GraphNeuralNetworkRegressor:
    """Scikit-Learn compatible Spatial Graph Neural Network (GNN) Regressor."""

    def __init__(
        self,
        hidden_dim: int = 64,
        max_epochs: int = 100,
        learning_rate: float = 0.005,
        batch_size: int = 256,
        top_k_neighbors: int = 8,
        random_state: int = 42
    ):
        self.hidden_dim = hidden_dim
        self.max_epochs = max_epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.top_k_neighbors = top_k_neighbors
        self.random_state = random_state

        self.input_dim_: int | None = None
        self.feature_means_: np.ndarray | None = None
        self.feature_stds_: np.ndarray | None = None
        self.target_mean_: float = 0.0
        self.target_std_: float = 1.0
        self.model_: Any = None
        self.weights_numpy_: dict[str, np.ndarray] | None = None

    def _compute_normalized_adjacency(self, X_batch: np.ndarray) -> np.ndarray:
        """Construct k-NN spatial route similarity adjacency matrix and compute normalized Graph Laplacian."""
        b, f = X_batch.shape
        # Pairwise cosine similarity / distance
        norms = np.linalg.norm(X_batch, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        X_normed = X_batch / norms

        sim = np.dot(X_normed, X_normed.T) # (b, b)
        
        # Keep top-k neighbors per sample to construct sparse spatial graph
        k = min(self.top_k_neighbors, b - 1)
        if k > 0:
            adj = np.zeros_like(sim)
            top_indices = np.argsort(sim, axis=1)[:, -k:]
            for row_idx in range(b):
                adj[row_idx, top_indices[row_idx]] = sim[row_idx, top_indices[row_idx]]
            adj = np.maximum(adj, adj.T) # Symmetric adjacency
        else:
            adj = np.eye(b)

        # Self-loops A_tilde = A + I
        adj_tilde = adj + np.eye(b)
        degrees = np.sum(adj_tilde, axis=1)
        degrees_inv_sqrt = np.power(degrees, -0.5)
        degrees_inv_sqrt[np.isinf(degrees_inv_sqrt)] = 0.0
        D_mat = np.diag(degrees_inv_sqrt)

        # Normalized Laplacian A_norm = D^(-1/2) * A_tilde * D^(-1/2)
        adj_norm = D_mat @ adj_tilde @ D_mat
        return adj_norm

    def _extract_numpy_gnn_features(self, X_norm: np.ndarray, wn: dict[str, np.ndarray]) -> np.ndarray:
        """Memory-efficient batch Graph Convolution message passing in NumPy."""
        n_samples = len(X_norm)
        gnn_chunks = []
        bs = self.batch_size

        for i in range(0, n_samples, bs):
            chunk = X_norm[i:i + bs]
            b = len(chunk)
            adj_norm = self._compute_normalized_adjacency(chunk)

            # GCN Layer 1: H1 = ELU( A_norm @ chunk @ W_gcn1 + b_gcn1 )
            support1 = np.dot(chunk, wn['W_gcn1']) + wn['b_gcn1']
            H1 = np.maximum(0, np.dot(adj_norm, support1)) # ELU/ReLU activation

            # GCN Layer 2: H2 = ELU( A_norm @ H1 @ W_gcn2 + b_gcn2 )
            support2 = np.dot(H1, wn['W_gcn2']) + wn['b_gcn2']
            H2 = np.maximum(0, np.dot(adj_norm, support2))

            gnn_representation = np.hstack([H1, H2, chunk])
            gnn_chunks.append(gnn_representation)

        return np.vstack(gnn_chunks)

    def fit(self, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray) -> GraphNeuralNetworkRegressor:
        """Fit GNN model on spatial trade features."""
        np.random.seed(self.random_state)

        if isinstance(X, pd.DataFrame):
            X_arr = X.to_numpy(dtype=np.float32)
        else:
            X_arr = np.array(X, dtype=np.float32)

        if isinstance(y, (pd.Series, pd.DataFrame)):
            y_arr = y.to_numpy(dtype=np.float32).flatten()
        else:
            y_arr = np.array(y, dtype=np.float32).flatten()

        n_samples, n_features = X_arr.shape
        self.input_dim_ = n_features

        # Standardize features and target
        self.feature_means_ = np.nanmean(X_arr, axis=0)
        self.feature_stds_ = np.nanstd(X_arr, axis=0)
        self.feature_stds_[self.feature_stds_ == 0] = 1.0

        X_norm = (X_arr - self.feature_means_) / self.feature_stds_
        X_norm = np.nan_to_num(X_norm, nan=0.0)

        self.target_mean_ = float(np.mean(y_arr))
        self.target_std_ = float(np.std(y_arr))
        if self.target_std_ == 0:
            self.target_std_ = 1.0

        y_norm = (y_arr - self.target_mean_) / self.target_std_

        if HAS_TORCH:
            torch.manual_seed(self.random_state)
            self.model_ = PyTorchGNNModule(
                input_dim=self.input_dim_,
                hidden_dim=self.hidden_dim
            )
            optimizer = optim.AdamW(self.model_.parameters(), lr=self.learning_rate, weight_decay=1e-4)
            criterion = nn.MSELoss()

            # Batch GCN Training
            bs = self.batch_size
            self.model_.train()
            for epoch in range(self.max_epochs):
                indices = np.arange(n_samples)
                np.random.shuffle(indices)
                for i in range(0, n_samples, bs):
                    batch_idx = indices[i:i + bs]
                    batch_x = torch.tensor(X_norm[batch_idx], dtype=torch.float32)
                    batch_y = torch.tensor(y_norm[batch_idx], dtype=torch.float32)

                    adj_norm_np = self._compute_normalized_adjacency(X_norm[batch_idx])
                    adj_norm_t = torch.tensor(adj_norm_np, dtype=torch.float32)

                    optimizer.zero_grad()
                    preds = self.model_(batch_x, adj_norm_t)
                    loss = criterion(preds, batch_y)
                    loss.backward()
                    optimizer.step()
        else:
            limit1 = np.sqrt(6 / (n_features + self.hidden_dim))
            W_gcn1 = np.random.uniform(-limit1, limit1, (n_features, self.hidden_dim))
            b_gcn1 = np.zeros(self.hidden_dim)

            limit2 = np.sqrt(6 / (self.hidden_dim + self.hidden_dim))
            W_gcn2 = np.random.uniform(-limit2, limit2, (self.hidden_dim, self.hidden_dim))
            b_gcn2 = np.zeros(self.hidden_dim)

            self.weights_numpy_ = {
                'W_gcn1': W_gcn1, 'b_gcn1': b_gcn1,
                'W_gcn2': W_gcn2, 'b_gcn2': b_gcn2
            }

            # Batch extract spatial GNN features
            gnn_features = self._extract_numpy_gnn_features(X_norm, self.weights_numpy_)

            # Fit regularized Ridge head on GNN spatial embeddings
            reg = 1e-3
            I = np.eye(gnn_features.shape[1])
            W_ridge = np.linalg.solve(gnn_features.T @ gnn_features + reg * I, gnn_features.T @ y_norm)
            self.weights_numpy_['W_ridge'] = W_ridge

        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict continuous target values using trained GNN model."""
        if isinstance(X, pd.DataFrame):
            X_arr = X.to_numpy(dtype=np.float32)
        else:
            X_arr = np.array(X, dtype=np.float32)

        X_norm = (X_arr - self.feature_means_) / self.feature_stds_
        X_norm = np.nan_to_num(X_norm, nan=0.0)

        if HAS_TORCH and self.model_ is not None:
            self.model_.eval()
            with torch.no_grad():
                n_samples = len(X_norm)
                bs = self.batch_size
                preds_list = []
                for i in range(0, n_samples, bs):
                    chunk = X_norm[i:i + bs]
                    adj_norm_np = self._compute_normalized_adjacency(chunk)
                    tensor_x = torch.tensor(chunk, dtype=torch.float32)
                    adj_norm_t = torch.tensor(adj_norm_np, dtype=torch.float32)
                    chunk_preds = self.model_(tensor_x, adj_norm_t).cpu().numpy()
                    preds_list.append(chunk_preds)
                preds_norm = np.concatenate(preds_list)
        elif self.weights_numpy_ is not None and 'W_ridge' in self.weights_numpy_:
            wn = self.weights_numpy_
            gnn_features = self._extract_numpy_gnn_features(X_norm, wn)
            preds_norm = gnn_features @ wn['W_ridge']
        else:
            preds_norm = np.zeros(len(X_arr))

        preds = preds_norm * self.target_std_ + self.target_mean_
        return preds
