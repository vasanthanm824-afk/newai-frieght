"""Smoke test — verify all components work end-to-end."""
import pickle
from pathlib import Path

from freight_pipeline import (
    INDIAN_EAST_COAST_PORTS, ORIGIN_PORTS, SAILING_DISTANCES_NM, VESSEL_CATALOG,
    create_demo_dataset, clean_dataset, engineer_features, forecast_rates,
    recommend_vessels, risk_alerts, understand_dataset,
)

print("[OK] freight_pipeline imports")

# Dataset
ds = create_demo_dataset()
print(f"[OK] Dataset: {ds.shape[0]} rows, {ds.shape[1]} cols")
print(f"     Dest ports: {sorted(ds.destination_port.unique())}")

# Model
model_path = Path("models/freight_model.pkl")
with model_path.open("rb") as f:
    payload = pickle.load(f)
model = payload["model"]
feature_columns = payload["feature_columns"]
metrics = payload["metrics"]
print(f"[OK] Model: R2={metrics['r2']:.4f}, MAE={metrics['mae']:.4f}")

# Forecast
fc = forecast_rates(model, "Australia", "Paradip", "Supramax", 50000, months=6, feature_columns=feature_columns)
print(f"[OK] Forecast: {len(fc)} months, avg=${fc['rate_usd_per_ton'].mean():.2f}")
print(f"     Bounds: lower=${fc['rate_lower'].mean():.2f}, upper=${fc['rate_upper'].mean():.2f}")

# Vessel recs per port
for port in ["Paradip", "Gangavaram", "Gopalpur", "Sagar-Sandheads", "Haldia"]:
    r = recommend_vessels("Australia", port, 50000, "Newcastle")
    types = r["vessel_type"].tolist() if not r.empty else []
    print(f"     {port}: {len(r)} feasible -> {types}")

# Contract optimizer
from contract_optimizer import analyze_market_entry, compare_contract_strategies, analyze_idle_scenarios
entry = analyze_market_entry(model, "Australia", "Paradip", "Supramax", 50000, 6, feature_columns)
print(f"[OK] Market entry: {entry.action} ({entry.confidence})")
contract = compare_contract_strategies(model, "Australia", "Paradip", "Supramax", 50000, 6, feature_columns)
print(f"[OK] Contract: Best={contract.recommended_strategy}")
print(f"     Savings vs spot: ${contract.savings_vs_spot:,.0f}")

# Voyage calculator
from voyage_calculator import compute_voyage_cost
vc = compute_voyage_cost("Australia", "Newcastle", "Paradip", "Supramax", 50000)
print(f"[OK] Voyage: ${vc.total_cost_usd:,.0f} total, {vc.total_voyage_days} days, ${vc.cost_per_tonne}/ton")

# Idle
idle = analyze_idle_scenarios(model, "Australia", "Paradip", "Supramax", 50000, feature_columns)
print(f"[OK] Idle: {idle.estimated_idle_days} days, cost=${idle.idle_cost_usd:,.0f}")

print()
print("=== ALL TESTS PASSED ===")
