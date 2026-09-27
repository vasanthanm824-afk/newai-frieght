"""Temporal Fusion Transformer (TFT) Regressor for Freight Time-Series Forecasting.

Features:
- Variable Selection Network (VSN) for dynamic feature selection
- Gated Residual Networks (GRN) for nonlinear feature processing
- Temporal Multi-Head Self-Attention Layer for feature & context aggregation
- Standard Scikit-Learn fit/predict interface compatible with ensemble models
- Supports PyTorch engine if available, with memory-efficient NumPy fallback
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd
from typing import Any

# Check for PyTorch availability
HAS_TORCH = False
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    pass


if HAS_TORCH:
    class GRNModule(nn.Module):
        """Gated Residual Network (GRN) PyTorch module."""
        def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float = 0.1):
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc2 = nn.Linear(hidden_dim, output_dim)
            self.gate = nn.Linear(input_dim, output_dim)
            self.layer_norm = nn.LayerNorm(output_dim)
            self.dropout = nn.Dropout(dropout)
            self.elu = nn.ELU()
            self.sigmoid = nn.Sigmoid()

            if input_dim != output_dim:
                self.residual_fc = nn.Linear(input_dim, output_dim)
            else:
                self.residual_fc = None

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            residual = self.residual_fc(x) if self.residual_fc is not None else x
            h = self.elu(self.fc1(x))
            h = self.dropout(self.fc2(h))
            g = self.sigmoid(self.gate(x))
            gated = h * g
            return self.layer_norm(residual + gated)

    class PyTorchTFTModule(nn.Module):
        """PyTorch Neural Network for Temporal Fusion Transformer architecture."""
        def __init__(self, input_dim: int, hidden_dim: int = 64, num_heads: int = 4, dropout: float = 0.1):
            super().__init__()
            self.input_dim = input_dim
            self.hidden_dim = hidden_dim

            # Feature input projections
            self.feature_encoder = nn.Linear(input_dim, hidden_dim)

            # Variable Selection Network (VSN)
            self.vsn_weights = nn.Linear(input_dim, input_dim)
            self.vsn_softmax = nn.Softmax(dim=-1)

            # Gated Residual Networks
            self.grn1 = GRNModule(hidden_dim, hidden_dim, hidden_dim, dropout)
            self.grn2 = GRNModule(hidden_dim, hidden_dim, hidden_dim, dropout)

            # Multi-Head Self-Attention over sequence/feature channels
            self.multihead_attn = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=num_heads, batch_first=True)
            self.attn_norm = nn.LayerNorm(hidden_dim)

            # Final Prediction Head
            self.head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ELU(),
                nn.Linear(hidden_dim // 2, 1)
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, input_dim)
            weights = self.vsn_softmax(self.vsn_weights(x))
            weighted_x = x * weights

            h = self.feature_encoder(weighted_x)
            h = self.grn1(h)

            h_seq = h.unsqueeze(1)
            attn_out, _ = self.multihead_attn(h_seq, h_seq, h_seq)
            h_attn = self.attn_norm(h_seq + attn_out).squeeze(1)

            h_out = self.grn2(h_attn)
            out = self.head(h_out)
            return out.squeeze(-1)


class TemporalFusionTransformerRegressor:
    """Scikit-Learn compatible Temporal Fusion Transformer (TFT) Regressor."""

    def __init__(
        self,
        hidden_dim: int = 64,
        num_heads: int = 4,
        max_epochs: int = 100,
        learning_rate: float = 0.005,
        batch_size: int = 256,
        random_state: int = 42
    ):
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.max_epochs = max_epochs
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.random_state = random_state

        self.input_dim_: int | None = None
        self.feature_means_: np.ndarray | None = None
        self.feature_stds_: np.ndarray | None = None
        self.target_mean_: float = 0.0
        self.target_std_: float = 1.0
        self.model_: Any = None
        self.weights_numpy_: dict[str, np.ndarray] | None = None

    def _extract_numpy_tft_features(self, X_norm: np.ndarray, wn: dict[str, np.ndarray]) -> np.ndarray:
        """Memory-efficient batch extraction of TFT latent representations using NumPy."""
        n_samples = len(X_norm)
        latent_chunks = []
        bs = self.batch_size
        head_dim = self.hidden_dim // self.num_heads

        for i in range(0, n_samples, bs):
            chunk = X_norm[i:i + bs]
            logits_vsn = np.dot(chunk, wn['W_vsn']) + wn['b_vsn']
            exp_vsn = np.exp(logits_vsn - np.max(logits_vsn, axis=-1, keepdims=True))
            weights_vsn = exp_vsn / np.sum(exp_vsn, axis=-1, keepdims=True)
            chunk_vsn = chunk * weights_vsn

            H = np.maximum(0, np.dot(chunk_vsn, wn['W_enc']) + wn['b_enc'])
            gate = 1.0 / (1.0 + np.exp(-np.dot(H, wn['W_gate'])))
            GRN_h = np.maximum(0, np.dot(H, wn['W_grn1']) + wn['b_grn1']) * gate

            b = len(chunk)
            GRN_heads = GRN_h.reshape(b, self.num_heads, head_dim)

            Q = np.einsum('b h d, h d k -> b h k', GRN_heads, wn['W_q_heads'])
            K = np.einsum('b h d, h d k -> b h k', GRN_heads, wn['W_k_heads'])
            V = np.einsum('b h d, h d k -> b h k', GRN_heads, wn['W_v_heads'])

            scores = np.einsum('b h d, b h k -> b h d k', Q, K) / np.sqrt(head_dim)
            attn_weights = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
            attn_weights = attn_weights / np.sum(attn_weights, axis=-1, keepdims=True)

            attn_heads = np.einsum('b h d k, b h k -> b h d', attn_weights, V)
            attn_out = attn_heads.reshape(b, self.hidden_dim)

            latent = np.hstack([GRN_h, attn_out, chunk])
            latent_chunks.append(latent)

        return np.vstack(latent_chunks)

    def fit(self, X: pd.DataFrame | np.ndarray, y: pd.Series | np.ndarray) -> TemporalFusionTransformerRegressor:
        """Fit TFT model on training data."""
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
            self.model_ = PyTorchTFTModule(
                input_dim=self.input_dim_,
                hidden_dim=self.hidden_dim,
                num_heads=self.num_heads
            )
            optimizer = optim.AdamW(self.model_.parameters(), lr=self.learning_rate, weight_decay=1e-4)
            criterion = nn.MSELoss()

            dataset = torch.utils.data.TensorDataset(
                torch.tensor(X_norm, dtype=torch.float32),
                torch.tensor(y_norm, dtype=torch.float32)
            )
            loader = torch.utils.data.DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

            self.model_.train()
            for epoch in range(self.max_epochs):
                for batch_x, batch_y in loader:
                    optimizer.zero_grad()
                    preds = self.model_(batch_x)
                    loss = criterion(preds, batch_y)
                    loss.backward()
                    optimizer.step()
        else:
            head_dim = self.hidden_dim // self.num_heads

            limit_vsn = np.sqrt(6 / (n_features + n_features))
            W_vsn = np.random.uniform(-limit_vsn, limit_vsn, (n_features, n_features))
            b_vsn = np.zeros(n_features)

            limit_enc = np.sqrt(6 / (n_features + self.hidden_dim))
            W_enc = np.random.uniform(-limit_enc, limit_enc, (n_features, self.hidden_dim))
            b_enc = np.zeros(self.hidden_dim)

            W_grn1 = np.random.uniform(-0.1, 0.1, (self.hidden_dim, self.hidden_dim))
            b_grn1 = np.zeros(self.hidden_dim)
            W_gate = np.random.uniform(-0.1, 0.1, (self.hidden_dim, self.hidden_dim))

            W_q_heads = np.random.uniform(-0.1, 0.1, (self.num_heads, head_dim, head_dim))
            W_k_heads = np.random.uniform(-0.1, 0.1, (self.num_heads, head_dim, head_dim))
            W_v_heads = np.random.uniform(-0.1, 0.1, (self.num_heads, head_dim, head_dim))

            self.weights_numpy_ = {
                'W_vsn': W_vsn, 'b_vsn': b_vsn,
                'W_enc': W_enc, 'b_enc': b_enc,
                'W_grn1': W_grn1, 'b_grn1': b_grn1,
                'W_gate': W_gate,
                'W_q_heads': W_q_heads, 'W_k_heads': W_k_heads, 'W_v_heads': W_v_heads
            }

            # Batch extract latent TFT features
            latent_features = self._extract_numpy_tft_features(X_norm, self.weights_numpy_)

            # Fit regularized Ridge head on TFT representations
            reg = 1e-3
            I = np.eye(latent_features.shape[1])
            W_ridge = np.linalg.solve(latent_features.T @ latent_features + reg * I, latent_features.T @ y_norm)
            self.weights_numpy_['W_ridge'] = W_ridge

        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict continuous target values using trained TFT model."""
        if isinstance(X, pd.DataFrame):
            X_arr = X.to_numpy(dtype=np.float32)
        else:
            X_arr = np.array(X, dtype=np.float32)

        X_norm = (X_arr - self.feature_means_) / self.feature_stds_
        X_norm = np.nan_to_num(X_norm, nan=0.0)

        if HAS_TORCH and self.model_ is not None:
            self.model_.eval()
            with torch.no_grad():
                tensor_x = torch.tensor(X_norm, dtype=torch.float32)
                preds_norm = self.model_(tensor_x).cpu().numpy()
        elif self.weights_numpy_ is not None and 'W_ridge' in self.weights_numpy_:
            wn = self.weights_numpy_
            latent_features = self._extract_numpy_tft_features(X_norm, wn)
            preds_norm = latent_features @ wn['W_ridge']
        else:
            preds_norm = np.zeros(len(X_arr))

        preds = preds_norm * self.target_std_ + self.target_mean_
        return preds
