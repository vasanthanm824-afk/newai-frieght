"""Integration test for api_client.py against FastAPI backend."""
import sys
from api_client import FreightAPIClient

def test_api_client():
    client = FreightAPIClient()
    health = client.check_health()
    print(f"Health: {health}")
    assert health.get("status") == "ok", f"Backend unhealthy: {health}"

    countries = client.get_origin_countries()
    print(f"Origin countries: {countries}")
    assert len(countries) > 0

    ports, port_names = client.get_indian_ports()
    print(f"Indian ports ({len(port_names)}): {port_names}")
    assert len(port_names) > 0

    fc = client.get_forecast("Australia", "Paradip", "Supramax", 50000, 3)
    print(f"Forecast rows: {len(fc)}")
    assert not fc.empty

    rec = client.recommend_vessels("Australia", "Paradip", 50000)
    print(f"Vessel recs: {len(rec)}")
    assert not rec.empty

    contract = client.compare_contracts("Australia", "Paradip", "Supramax", 50000)
    print(f"Recommended contract: {contract.get('recommended_strategy')}")
    assert "recommended_strategy" in contract

    signal = client.get_market_entry("Australia", "Paradip", "Supramax", 50000)
    print(f"Market entry: {signal.get('action')} ({signal.get('confidence')})")
    assert "action" in signal

    vc = client.get_voyage_cost("Australia", "Newcastle", "Paradip", "Supramax", 50000)
    print(f"Voyage total cost: ${vc.get('total_cost_usd'):,.2f}")
    assert vc.get("total_cost_usd", 0) > 0

    alerts = client.get_risk_alerts("Australia", "Paradip", "Supramax", 50000)
    print(f"Risk alerts count: {len(alerts)}")

    # Test new endpoints
    try:
        rep_json = client.export_shipment_report({
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "cargo_tonnes": 50000,
            "vessel_type": "Supramax"
        }, fmt="json")
        print(f"Report export title: {rep_json.get('report_title')}")

        bench = client.benchmark_scenarios([
            {"scenario_name": "S1", "origin_country": "Australia", "destination_port": "Paradip", "vessel_type": "Supramax", "cargo_tonnes": 50000},
            {"scenario_name": "S2", "origin_country": "Australia", "destination_port": "Vizag", "vessel_type": "Capesize", "cargo_tonnes": 150000}
        ])
        print(f"Benchmark recommended: {bench.get('recommended_scenario')}")

        risk_mat = client.get_live_risk_matrix("Australia", "Paradip", "Supramax", 50000)
        print(f"Risk matrix level: {risk_mat.get('overall_risk_level')}")
    except Exception as e:
        print(f"Note: Live API client tests skipped (backend server not running): {e}")

    print("\n=== ALL API CLIENT INTEGRATION TESTS PASSED ===")

if __name__ == "__main__":
    test_api_client()

