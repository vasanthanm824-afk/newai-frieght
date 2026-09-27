"""Quick API endpoint test."""
import requests, json

base = "http://localhost:8000"

r = requests.get(f"{base}/api/health")
print(f"Health: {r.json()}")

r = requests.get(f"{base}/api/ports/indian")
ports = list(r.json()["ports"].keys())
print(f"Indian ports: {ports}")

r = requests.post(f"{base}/api/forecast", json={"origin_country":"Australia","destination_port":"Paradip","vessel_type":"Supramax","cargo_tonnes":50000,"months":3})
fc = r.json()["forecast"]
print(f"Forecast: {len(fc)} months, rate=${fc[0]['rate_usd_per_ton']:.2f}")

r = requests.post(f"{base}/api/contracts/market-entry", json={"origin_country":"Australia","destination_port":"Paradip","vessel_type":"Supramax","cargo_tonnes":50000})
sig = r.json()["signal"]
print(f"Signal: {sig['action']} ({sig['confidence']})")

print("ALL API TESTS PASSED")
