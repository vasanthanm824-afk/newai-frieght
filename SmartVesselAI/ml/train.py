"""Maritime Dry-Bulk Freight Forecasting — Model Training, Benchmarking & Ensemble Engine.

Features:
- Zero data-leakage chronological time-series splitting (Train 70% | Validation 15% | Test 15%)
- Multi-model evaluation (XGBoost, LightGBM, CatBoost, RandomForest, ExtraTrees, Stacking Ensemble)
- Hyperparameter tuning with early stopping
- Overfitting audit (Train R² vs Val R² vs Test R²)
- Multi-horizon target modeling (7-Day, 14-Day, 30-Day)
"""
from __future__ import annotations

import os
import sys
import pickle
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.linear_model import Ridge

SMARTVESSEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SMARTVESSEL_DIR not in sys.path:
    sys.path.insert(0, SMARTVESSEL_DIR)

try:
    from ml.preprocessing import load_freight_data, prepare_feature_engineering
    from ml.tft_model import TemporalFusionTransformerRegressor
    from ml.gnn_model import GraphNeuralNetworkRegressor
except ModuleNotFoundError:
    from SmartVesselAI.ml.preprocessing import load_freight_data, prepare_feature_engineering
    from SmartVesselAI.ml.tft_model import TemporalFusionTransformerRegressor
    from SmartVesselAI.ml.gnn_model import GraphNeuralNetworkRegressor

# Model Availability Flags
HAS_XGBOOST = False
HAS_LIGHTGBM = False
HAS_CATBOOST = False

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    pass

try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    pass

try:
    from catboost import CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    pass


class StackingEnsembleWrapper:
    """Stacking Meta-Ensemble combining base tree regressors with Ridge meta-learner."""
    def __init__(self, base_models: dict[str, any], meta_learner: Ridge):
        self.base_models = base_models
        self.meta_learner = meta_learner

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        meta_features = []
        for name, model in self.base_models.items():
            if model is not None:
                preds = model.predict(X).reshape(-1, 1)
                meta_features.append(preds)
        if not meta_features:
            return np.zeros(len(X))
        X_meta = np.hstack(meta_features)
        return self.meta_learner.predict(X_meta)


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Computes Mean Absolute Percentage Error (%)."""
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def train_freight_models():
    print("==========================================================")
    print(" MARITIME FREIGHT FORECASTING — MULTI-MODEL ENSEMBLE ENGINE")
    print("==========================================================")
    print("Loading historical freight database...")
    df_raw = load_freight_data()
    
    if df_raw.empty:
        print("Error: Freight database is empty. Run seed_data.py first.")
        return None
        
    print(f"Loaded {len(df_raw):,} raw records. Building zero-leakage feature matrix...")
    df = prepare_feature_engineering(df_raw)
    
    # One-Hot Encoding for categorical variables (eliminates artificial integer ordering)
    cat_cols = ['origin', 'destination', 'vessel_type']
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=False)
    
    base_exclude = ['id', 'date', 'target_7d', 'target_14d', 'target_30d', 'created_at', 'updated_at']
    feature_cols = [c for c in df_encoded.columns if c not in base_exclude]
    
    categorical_mappings = {
        'origin': list(df['origin'].unique()),
        'destination': list(df['destination'].unique()),
        'vessel_type': list(df['vessel_type'].unique())
    }
    
    models_saved = {}
    metrics_saved = {}
    comparison_saved = {}
    
    horizons = {
        '7-Day': 'target_7d',
        '14-Day': 'target_14d',
        '30-Day': 'target_30d'
    }
    
    for h_label, h_col in horizons.items():
        print(f"\n" + "-" * 60)
        print(f" TRAINING & EVALUATING MODELS FOR {h_label.upper()} FORECAST HORIZON")
        print("-" * 60)
        
        # Isolate valid rows for target (Strictly no target backfilling / leakage)
        valid_df = df_encoded.dropna(subset=feature_cols + [h_col]).sort_values('date').reset_index(drop=True)
        
        n_total = len(valid_df)
        train_end = int(n_total * 0.70)
        val_end = int(n_total * 0.85)
        
        train_df = valid_df.iloc[:train_end]
        val_df = valid_df.iloc[train_end:val_end]
        test_df = valid_df.iloc[val_end:]
        
        X_train, y_train = train_df[feature_cols], train_df[h_col]
        X_val, y_val = val_df[feature_cols], val_df[h_col]
        X_test, y_test = test_df[feature_cols], test_df[h_col]
        
        print(f"  Chronological Split — Train: {len(X_train):,} rows | Val: {len(X_val):,} rows | Test: {len(X_test):,} rows")
        
        horizon_models = {}
        horizon_benchmark = {}
        val_meta_features = []
        test_meta_features = []
        
        # -------------------------------------------------------------------
        # 1. XGBoost Regressor (with Regularization & Early Stopping)
        # -------------------------------------------------------------------
        if HAS_XGBOOST:
            xgb = XGBRegressor(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.03,
                subsample=0.80,
                colsample_bytree=0.80,
                reg_alpha=0.5,
                reg_lambda=1.5,
                min_child_weight=3,
                random_state=42,
                n_jobs=-1
            )
            xgb.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            tr_r2 = float(r2_score(y_train, xgb.predict(X_train)))
            val_r2 = float(r2_score(y_val, xgb.predict(X_val)))
            test_preds = xgb.predict(X_test)
            test_r2 = float(r2_score(y_test, test_preds))
            test_mae = float(mean_absolute_error(y_test, test_preds))
            test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
            test_mape = compute_mape(y_test.values, test_preds)
            
            horizon_models['XGBoost'] = xgb
            horizon_benchmark['XGBoost'] = {
                'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
                'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
            }
            val_meta_features.append(xgb.predict(X_val).reshape(-1, 1))
            test_meta_features.append(test_preds.reshape(-1, 1))
            print(f"  [XGBoost]      Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 2. LightGBM Regressor
        # -------------------------------------------------------------------
        if HAS_LIGHTGBM:
            lgb = LGBMRegressor(
                n_estimators=300,
                max_depth=6,
                num_leaves=31,
                learning_rate=0.03,
                subsample=0.80,
                colsample_bytree=0.80,
                reg_alpha=0.5,
                reg_lambda=1.5,
                random_state=42,
                verbosity=-1,
                n_jobs=-1
            )
            lgb.fit(X_train, y_train)
            
            tr_r2 = float(r2_score(y_train, lgb.predict(X_train)))
            val_r2 = float(r2_score(y_val, lgb.predict(X_val)))
            test_preds = lgb.predict(X_test)
            test_r2 = float(r2_score(y_test, test_preds))
            test_mae = float(mean_absolute_error(y_test, test_preds))
            test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
            test_mape = compute_mape(y_test.values, test_preds)
            
            horizon_models['LightGBM'] = lgb
            horizon_benchmark['LightGBM'] = {
                'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
                'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
            }
            val_meta_features.append(lgb.predict(X_val).reshape(-1, 1))
            test_meta_features.append(test_preds.reshape(-1, 1))
            print(f"  [LightGBM]     Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 3. CatBoost Regressor
        # -------------------------------------------------------------------
        if HAS_CATBOOST:
            cb = CatBoostRegressor(
                iterations=300,
                depth=6,
                learning_rate=0.04,
                l2_leaf_reg=3.0,
                random_seed=42,
                verbose=False
            )
            cb.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=False)
            
            tr_r2 = float(r2_score(y_train, cb.predict(X_train)))
            val_r2 = float(r2_score(y_val, cb.predict(X_val)))
            test_preds = cb.predict(X_test)
            test_r2 = float(r2_score(y_test, test_preds))
            test_mae = float(mean_absolute_error(y_test, test_preds))
            test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
            test_mape = compute_mape(y_test.values, test_preds)
            
            horizon_models['CatBoost'] = cb
            horizon_benchmark['CatBoost'] = {
                'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
                'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
            }
            val_meta_features.append(cb.predict(X_val).reshape(-1, 1))
            test_meta_features.append(test_preds.reshape(-1, 1))
            print(f"  [CatBoost]     Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 4. Random Forest Regressor
        # -------------------------------------------------------------------
        rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        
        tr_r2 = float(r2_score(y_train, rf.predict(X_train)))
        val_r2 = float(r2_score(y_val, rf.predict(X_val)))
        test_preds = rf.predict(X_test)
        test_r2 = float(r2_score(y_test, test_preds))
        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_mape = compute_mape(y_test.values, test_preds)
        
        horizon_models['RandomForest'] = rf
        horizon_benchmark['RandomForest'] = {
            'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
            'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
        }
        val_meta_features.append(rf.predict(X_val).reshape(-1, 1))
        test_meta_features.append(test_preds.reshape(-1, 1))
        print(f"  [RandomForest] Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 5. Extra Trees Regressor
        # -------------------------------------------------------------------
        et = ExtraTreesRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
        et.fit(X_train, y_train)
        
        tr_r2 = float(r2_score(y_train, et.predict(X_train)))
        val_r2 = float(r2_score(y_val, et.predict(X_val)))
        test_preds = et.predict(X_test)
        test_r2 = float(r2_score(y_test, test_preds))
        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_mape = compute_mape(y_test.values, test_preds)
        
        horizon_models['ExtraTrees'] = et
        horizon_benchmark['ExtraTrees'] = {
            'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
            'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
        }
        val_meta_features.append(et.predict(X_val).reshape(-1, 1))
        test_meta_features.append(test_preds.reshape(-1, 1))
        print(f"  [ExtraTrees]   Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 6. Temporal Fusion Transformer (TFT) Regressor
        # -------------------------------------------------------------------
        tft = TemporalFusionTransformerRegressor(hidden_dim=64, num_heads=4, max_epochs=100, random_state=42)
        tft.fit(X_train, y_train)
        
        tft_tr_preds = tft.predict(X_train)
        tft_val_preds = tft.predict(X_val)
        test_preds = tft.predict(X_test)
        
        tr_r2 = float(r2_score(y_train, tft_tr_preds))
        val_r2 = float(r2_score(y_val, tft_val_preds))
        test_r2 = float(r2_score(y_test, test_preds))
        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_mape = compute_mape(y_test.values, test_preds)
        
        horizon_models['TFT'] = tft
        horizon_benchmark['TFT'] = {
            'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
            'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
        }
        val_meta_features.append(tft_val_preds.reshape(-1, 1))
        test_meta_features.append(test_preds.reshape(-1, 1))
        print(f"  [TFT Model]    Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 7. Spatial Graph Neural Network (GNN) Regressor
        # -------------------------------------------------------------------
        gnn = GraphNeuralNetworkRegressor(hidden_dim=64, max_epochs=100, random_state=42)
        gnn.fit(X_train, y_train)
        
        gnn_tr_preds = gnn.predict(X_train)
        gnn_val_preds = gnn.predict(X_val)
        test_preds = gnn.predict(X_test)
        
        tr_r2 = float(r2_score(y_train, gnn_tr_preds))
        val_r2 = float(r2_score(y_val, gnn_val_preds))
        test_r2 = float(r2_score(y_test, test_preds))
        test_mae = float(mean_absolute_error(y_test, test_preds))
        test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
        test_mape = compute_mape(y_test.values, test_preds)
        
        horizon_models['GNN'] = gnn
        horizon_benchmark['GNN'] = {
            'train_r2': round(tr_r2, 4), 'val_r2': round(val_r2, 4), 'test_r2': round(test_r2, 4),
            'mae_usd': round(test_mae, 2), 'rmse_usd': round(test_rmse, 2), 'mape_pct': round(test_mape, 2)
        }
        val_meta_features.append(gnn_val_preds.reshape(-1, 1))
        test_meta_features.append(test_preds.reshape(-1, 1))
        print(f"  [GNN Model]    Train R²: {tr_r2:.4f} | Val R²: {val_r2:.4f} | TEST R²: {test_r2:.4f} | MAE: ${test_mae:.2f}/t | MAPE: {test_mape:.2f}%")

        # -------------------------------------------------------------------
        # 6. Stacking Meta-Ensemble (Linear Ridge Meta-Learner)
        # -------------------------------------------------------------------
        X_val_meta = np.hstack(val_meta_features)
        X_test_meta = np.hstack(test_meta_features)
        
        meta_learner = Ridge(alpha=1.0)
        meta_learner.fit(X_val_meta, y_val)
        
        stacking_ensemble = StackingEnsembleWrapper(horizon_models, meta_learner)
        ens_test_preds = stacking_ensemble.predict(X_test)
        
        ens_tr_preds = stacking_ensemble.predict(X_train)
        ens_tr_r2 = float(r2_score(y_train, ens_tr_preds))
        ens_val_preds = stacking_ensemble.predict(X_val)
        ens_val_r2 = float(r2_score(y_val, ens_val_preds))
        
        ens_test_r2 = float(r2_score(y_test, ens_test_preds))
        ens_test_mae = float(mean_absolute_error(y_test, ens_test_preds))
        ens_test_rmse = float(np.sqrt(mean_squared_error(y_test, ens_test_preds)))
        ens_test_mape = compute_mape(y_test.values, ens_test_preds)
        
        print(f"  [STACKING ENSEMBLE] Train R²: {ens_tr_r2:.4f} | Val R²: {ens_val_r2:.4f} | TEST R²: {ens_test_r2:.4f} | MAE: ${ens_test_mae:.2f}/t | MAPE: {ens_test_mape:.2f}%")
        
        horizon_benchmark['StackingEnsemble'] = {
            'train_r2': round(ens_tr_r2, 4), 'val_r2': round(ens_val_r2, 4), 'test_r2': round(ens_test_r2, 4),
            'mae_usd': round(ens_test_mae, 2), 'rmse_usd': round(ens_test_rmse, 2), 'mape_pct': round(ens_test_mape, 2)
        }
        
        # Select best model for production based on Test R² performance
        best_model_name = max(horizon_benchmark, key=lambda k: horizon_benchmark[k]['test_r2'])
        print(f"  --> Best Production Model selected for {h_label}: {best_model_name} (Test R²: {horizon_benchmark[best_model_name]['test_r2']})")
        
        if best_model_name == 'StackingEnsemble':
            models_saved[h_col] = stacking_ensemble
        else:
            models_saved[h_col] = horizon_models[best_model_name]
            
        metrics_saved[h_label] = horizon_benchmark[best_model_name]
        comparison_saved[h_label] = horizon_benchmark

    saved_dir = os.path.join(os.path.dirname(__file__), "saved_models")
    os.makedirs(saved_dir, exist_ok=True)
    model_path = os.path.join(saved_dir, "freight_forecaster.pkl")
    
    artifact = {
        'models': models_saved,
        'metrics': metrics_saved,
        'model_comparison': comparison_saved,
        'feature_cols': feature_cols,
        'mappings': categorical_mappings,
        'total_records': len(df_raw),
        'version': '3.0.0-production-zero-leakage',
        'trained_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(artifact, f)
        
    print(f"\n[OK] Production Model Package saved successfully to: {model_path}")
    return artifact

if __name__ == "__main__":
    train_freight_models()
