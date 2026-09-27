"""Unit & Integration test for new backend functional endpoints using FastAPI TestClient."""
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root directory is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.main import app

def test_new_backend_endpoints():
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[OK] Health endpoint passed:", res.json()["status"], flush=True)

        # 2. Report Export JSON
        export_payload = {
            "origin_country": "Australia",
            "destination_country": "India",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "cargo_tonnes": 50000,
            "vessel_type": "Supramax",
            "forecast_months": 3,
            "format": "json"
        }
        res = client.post("/api/reports/export", json=export_payload)
        assert res.status_code == 200, f"Export JSON failed: {res.text}"
        data = res.json()
        assert data.get("status") == "success"
        assert "summary" in data
        print("[OK] Report export (JSON) endpoint passed:", data["report_title"], flush=True)

        # 3. Report Export CSV
        export_payload["format"] = "csv"
        res = client.post("/api/reports/export", json=export_payload)
        assert res.status_code == 200, f"Export CSV failed: {res.text}"
        assert "SHIPMENT ANALYTICS SUMMARY REPORT" in res.text
        assert "text/csv" in res.headers.get("content-type", "")
        print("[OK] Report export (CSV) endpoint passed:", len(res.text), "bytes", flush=True)

        # 4. Multi-Scenario Benchmarking
        benchmark_payload = {
            "scenarios": [
                {
                    "scenario_name": "Base Supramax Paradip",
                    "origin_country": "Australia",
                    "destination_port": "Paradip",
                    "vessel_type": "Supramax",
                    "cargo_tonnes": 50000,
                    "voyages_per_year": 6
                },
                {
                    "scenario_name": "Capesize Vizag High Volume",
                    "origin_country": "Australia",
                    "destination_port": "Vizag",
                    "vessel_type": "Capesize",
                    "cargo_tonnes": 150000,
                    "voyages_per_year": 4
                }
            ]
        }
        res = client.post("/api/contracts/benchmark", json=benchmark_payload)
        assert res.status_code == 200, f"Benchmark failed: {res.text}"
        b_data = res.json()
        assert b_data.get("status") == "success", f"Benchmark status error: {b_data}"
        assert len(b_data.get("results", [])) == 2
        print("[OK] Scenario benchmarking endpoint passed. Recommended:", b_data.get("recommended_scenario"), flush=True)

        # 5. Live Structured Risk Matrix
        risk_payload = {
            "origin_country": "Australia",
            "destination_port": "Gopalpur",
            "vessel_type": "Capesize",
            "cargo_tonnes": 150000,
            "months": 6
        }
        res = client.post("/api/risk/live-alerts", json=risk_payload)
        assert res.status_code == 200, f"Live alerts failed: {res.text}"
        r_data = res.json()
        assert r_data.get("status") == "success"
        assert "risk_matrix" in r_data
        assert len(r_data["risk_matrix"]) >= 4
        print("[OK] Live risk matrix endpoint passed. Overall risk level:", r_data.get("overall_risk_level"), flush=True)

        # 6. Voyage Billing Endpoint Test
        billing_payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Panamax",
            "cargo_tonnes": 80000,
            "spot_rate_per_ton": 25.50,
            "discount_pct": 5.0,
            "tax_pct": 5.0
        }
        res = client.post("/api/voyage/billing", json=billing_payload)
        assert res.status_code == 200, f"Billing endpoint failed: {res.text}"
        bill_data = res.json()
        assert bill_data.get("status") == "success"
        bs = bill_data.get("billing_summary", {})
        assert bs.get("grand_total_usd", 0) > 0
        assert len(bs.get("line_items", [])) >= 5
        assert "formatted_text_invoice" in bs
        print("[OK] Voyage Billing endpoint passed. Invoice:", bill_data.get("invoice_number"), "Grand Total USD: $" + f"{bs.get('grand_total_usd'):,.2f}", flush=True)
        print("\n--- SAMPLE HUMAN READABLE PRO-FORMA INVOICE STATEMENT ---")
        print(bs.get("formatted_text_invoice")[:500] + "...\n", flush=True)

        print("\n=== ALL NEW BACKEND ENDPOINT TESTS PASSED ===", flush=True)

if __name__ == "__main__":
    test_new_backend_endpoints()
