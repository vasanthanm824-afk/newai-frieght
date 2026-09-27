from __future__ import annotations

import json
import pickle
from pathlib import Path

try:
    from .core.freight_pipeline import clean_dataset, create_demo_dataset, engineer_features, train_ml_model
except ImportError:
    from core.freight_pipeline import clean_dataset, create_demo_dataset, engineer_features, train_ml_model

MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "freight_model.pkl"
METRICS_PATH = MODEL_DIR / "freight_model_metrics.json"


def train_and_save_model() -> dict:
    """Train the freight forecasting model and save artifacts."""
    print("Generating realistic demo dataset...")
    dataset = create_demo_dataset()
    print(f"  Dataset shape: {dataset.shape}")

    print("Cleaning dataset...")
    cleaned = clean_dataset(dataset)
    print(f"  Cleaned shape: {cleaned.shape}")

    print("Engineering features...")
    features = engineer_features(cleaned)
    print(f"  Feature count: {len(features.columns)}")

    print("Training Temporal Fusion Transformer (TFT) model...")
    model, metrics, _, _ = train_ml_model(features, model_type="tft")
    print(f"  MAE:  {metrics['mae']:.4f}")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  R²:   {metrics['r2']:.4f}")

    # Determine feature columns (exclude non-numeric and target)
    target = "rate_usd_per_ton"
    exclude = {
        target, "shipment_date", "origin_country", "destination_country",
        "vessel_type", "origin_port", "destination_port",
    }
    feature_columns = [col for col in features.columns if col not in exclude]

    payload = {
        "model": model,
        "feature_columns": feature_columns,
        "metrics": metrics,
    }

    with MODEL_PATH.open("wb") as file:
        pickle.dump(payload, file)

    with METRICS_PATH.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print(f"\nModel saved to: {MODEL_PATH}")
    return {"model_path": str(MODEL_PATH), "metrics": metrics}


if __name__ == "__main__":
    result = train_and_save_model()
    print(json.dumps(result["metrics"], indent=2))
