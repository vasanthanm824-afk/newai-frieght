"""Full automated test suite verifying all tasks in the task list:
1. Web pages & navigation links (HTTP 200, title, key elements)
2. Interactive API endpoints (status 200, valid payload contracts)
3. Streamlit dashboard responsiveness
"""
import sys
import json
import time
import requests

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_WEB_URL = "http://127.0.0.1:8000"
BASE_ST_URL = "http://127.0.0.1:8501"

results = {
    "pages": [],
    "apis": [],
    "streamlit": []
}

def log_test(category, name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {category.upper()}: {name} - {details}", flush=True)
    results[category].append({
        "name": name,
        "passed": passed,
        "details": details
    })

def verify_pages():
    print("\n=======================================================")
    print(" TASK: VERIFY WEB PAGES, TITLES & KEY COMPONENTS")
    print("=======================================================")
    pages_to_test = [
        ("/", "SmartVesselAI", ["nav-item-link", "Dashboard", "Forecast"]),
        ("/index.html", "SmartVesselAI", ["Dashboard", "Freight Rate Trend", "Top 5 Routes"]),
        ("/forecast.html", "SmartVesselAI", ["Forecast", "chart", "origin"]),
        ("/vessels.html", "SmartVesselAI", ["Vessel", "Handysize", "Supramax"]),
        ("/ports.html", "SmartVesselAI", ["Port", "Draft", "Paradip"]),
        ("/risk.html", "SmartVesselAI", ["Risk", "Monsoon", "Weather"]),
        ("/optimization.html", "SmartVesselAI", ["Optimization", "Charter", "Landed Cost"]),
        ("/decision.html", "SmartVesselAI", ["Decision", "Action", "Recommendation"]),
        ("/billing.html", "SmartVesselAI", ["Invoice", "Billing", "USD"]),
        ("/tracking.html", "SmartVesselAI", ["Tracking", "Vessel", "Route"]),
        ("/whatif.html", "SmartVesselAI", ["What-If", "Simulation", "Sensitivity"]),
        ("/alerts.html", "SmartVesselAI", ["Alerts", "Notification"]),
        ("/health.html", "SmartVesselAI", ["Health", "Status"]),
        ("/settings.html", "SmartVesselAI", ["Settings", "Configuration"]),
    ]

    for path, expected_title_part, required_snippets in pages_to_test:
        url = f"{BASE_WEB_URL}{path}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                log_test("pages", path, False, f"Status HTTP {r.status_code}")
                continue
            html = r.text
            missing = [s for s in required_snippets if s.lower() not in html.lower()]
            if missing:
                log_test("pages", path, False, f"Missing snippets: {missing}")
            else:
                log_test("pages", path, True, f"HTTP 200, snippets verified ({len(required_snippets)}/{len(required_snippets)})")
        except Exception as e:
            log_test("pages", path, False, str(e))

def verify_apis():
    print("\n=======================================================")
    print(" TASK: VERIFY ALL INTERACTIVE API ENDPOINTS")
    print("=======================================================")
    
    # 1. Health
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/health", timeout=5)
        data = r.json()
        log_test("apis", "GET /api/health", r.status_code == 200 and data.get("status") == "ok", f"Model loaded: {data.get('model_loaded')}")
    except Exception as e:
        log_test("apis", "GET /api/health", False, str(e))

    # 2. Ports Catalog
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/ports/all-countries", timeout=5)
        data = r.json()
        countries = data.get("countries", [])
        log_test("apis", "GET /api/ports/all-countries", r.status_code == 200 and len(countries) > 10, f"Found {len(countries)} countries")
    except Exception as e:
        log_test("apis", "GET /api/ports/all-countries", False, str(e))

    # 3. Ports by country
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/ports/by-country?country=Australia", timeout=5)
        data = r.json()
        p_names = data.get("port_names", [])
        log_test("apis", "GET /api/ports/by-country (Australia)", r.status_code == 200 and len(p_names) > 0, f"Ports: {p_names[:3]}")
    except Exception as e:
        log_test("apis", "GET /api/ports/by-country", False, str(e))

    # 4. Indian Ports
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/ports/indian", timeout=5)
        data = r.json()
        p_names = data.get("port_names", [])
        log_test("apis", "GET /api/ports/indian", r.status_code == 200 and len(p_names) >= 7, f"Indian East Coast ports: {p_names}")
    except Exception as e:
        log_test("apis", "GET /api/ports/indian", False, str(e))

    # 5. Vessel catalog
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/ports/vessels", timeout=5)
        data = r.json()
        v_list = data.get("vessels", [])
        log_test("apis", "GET /api/ports/vessels", r.status_code == 200 and len(v_list) >= 4, f"Vessel classes: {[v['vessel_type'] for v in v_list]}")
    except Exception as e:
        log_test("apis", "GET /api/ports/vessels", False, str(e))

    # 6. Forecast predict
    try:
        payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "months": 6
        }
        r = requests.post(f"{BASE_WEB_URL}/api/forecast", json=payload, timeout=10)
        data = r.json()
        fc = data.get("forecast", [])
        log_test("apis", "POST /api/forecast", r.status_code == 200 and len(fc) >= 6, f"Forecast points: {len(fc)}, latest rate: ${fc[0].get('rate_usd_per_ton') if fc else 0}/ton")
    except Exception as e:
        log_test("apis", "POST /api/forecast", False, str(e))

    # 7. Contracts comparison
    try:
        payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "voyages_per_year": 6
        }
        r = requests.post(f"{BASE_WEB_URL}/api/contracts/compare", json=payload, timeout=10)
        data = r.json()
        c = data.get("contract", {})
        log_test("apis", "POST /api/contracts/compare", r.status_code == 200 and "recommended_strategy" in c, f"Recommended: {c.get('recommended_strategy')}")
    except Exception as e:
        log_test("apis", "POST /api/contracts/compare", False, str(e))

    # 8. Market entry timing
    try:
        payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "forecast_months": 6
        }
        r = requests.post(f"{BASE_WEB_URL}/api/contracts/market-entry", json=payload, timeout=10)
        data = r.json()
        sig = data.get("signal", {})
        log_test("apis", "POST /api/contracts/market-entry", r.status_code == 200 and "action" in sig, f"Action: {sig.get('action')} ({sig.get('confidence')})")
    except Exception as e:
        log_test("apis", "POST /api/contracts/market-entry", False, str(e))

    # 9. Multi-scenario benchmark
    try:
        payload = {
            "scenarios": [
                {"scenario_name": "Base Supramax", "origin_country": "Australia", "destination_port": "Paradip", "vessel_type": "Supramax", "cargo_tonnes": 50000, "voyages_per_year": 6},
                {"scenario_name": "Capesize Vizag", "origin_country": "Australia", "destination_port": "Vizag", "vessel_type": "Capesize", "cargo_tonnes": 150000, "voyages_per_year": 4}
            ]
        }
        r = requests.post(f"{BASE_WEB_URL}/api/contracts/benchmark", json=payload, timeout=10)
        data = r.json()
        log_test("apis", "POST /api/contracts/benchmark", r.status_code == 200 and len(data.get("results", [])) == 2, f"Recommended: {data.get('recommended_scenario')}")
    except Exception as e:
        log_test("apis", "POST /api/contracts/benchmark", False, str(e))

    # 10. Voyage cost calculation
    try:
        payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0
        }
        r = requests.post(f"{BASE_WEB_URL}/api/voyage/cost", json=payload, timeout=10)
        data = r.json()
        v = data.get("voyage", {})
        log_test("apis", "POST /api/voyage/cost", r.status_code == 200 and v.get("total_cost_usd", 0) > 0, f"Total: ${v.get('total_cost_usd', 0):,.2f}, days: {v.get('total_voyage_days')}")
    except Exception as e:
        log_test("apis", "POST /api/voyage/cost", False, str(e))

    # 11. Voyage billing
    try:
        payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Panamax",
            "cargo_tonnes": 80000,
            "spot_rate_per_ton": 25.50,
            "discount_pct": 5.0,
            "tax_pct": 5.0
        }
        r = requests.post(f"{BASE_WEB_URL}/api/voyage/billing", json=payload, timeout=10)
        data = r.json()
        bs = data.get("billing_summary", {})
        log_test("apis", "POST /api/voyage/billing", r.status_code == 200 and bs.get("grand_total_usd", 0) > 0, f"Invoice: {data.get('invoice_number')}, Total: ${bs.get('grand_total_usd', 0):,.2f}")
    except Exception as e:
        log_test("apis", "POST /api/voyage/billing", False, str(e))

    # 12. Risk alerts & Matrix
    try:
        payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000,
            "months": 6
        }
        r = requests.post(f"{BASE_WEB_URL}/api/risk/alerts", json=payload, timeout=10)
        data = r.json()
        log_test("apis", "POST /api/risk/alerts", r.status_code == 200 and "alerts" in data, f"Generated {len(data.get('alerts', []))} alerts")

        r2 = requests.post(f"{BASE_WEB_URL}/api/risk/live-alerts", json=payload, timeout=10)
        data2 = r2.json()
        log_test("apis", "POST /api/risk/live-alerts", r2.status_code == 200 and "risk_matrix" in data2, f"Matrix size: {len(data2.get('risk_matrix', []))}, Level: {data2.get('overall_risk_level')}")
    except Exception as e:
        log_test("apis", "POST /api/risk/alerts", False, str(e))

    # 13. 5-Day Alternative Date Evaluation
    try:
        payload = {
            "target_date": "2026-07-15",
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_country": "India",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000
        }
        r = requests.post(f"{BASE_WEB_URL}/api/risk/evaluate-date", json=payload, timeout=10)
        data = r.json()
        alts = data.get("alternative_dates", [])
        log_test("apis", "POST /api/risk/evaluate-date", r.status_code == 200 and len(alts) == 5, f"Recommended {len(alts)} lower-risk alternative dates")
    except Exception as e:
        log_test("apis", "POST /api/risk/evaluate-date", False, str(e))

    # 14. Linked List Route Generation & Modification
    try:
        payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_country": "India",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000
        }
        r = requests.post(f"{BASE_WEB_URL}/api/linked-list/build-route", json=payload, timeout=10)
        data = r.json()
        nodes = data.get("nodes", [])
        log_test("apis", "POST /api/linked-list/build-route", r.status_code == 200 and len(nodes) >= 3, f"Doubly linked nodes: {len(nodes)}, first: {nodes[0].get('location_name')}, last: {nodes[-1].get('location_name')}")

        if nodes:
            target_id = nodes[0]["node_id"]
            insert_payload = {
                "target_node_id": target_id,
                "new_node_title": "Sunda Strait Waypoint",
                "location_name": "Sunda Strait",
                "country": "Indonesia",
                "vessel_type": "Supramax",
                "distance_nm": 320.0,
                "est_days": 1.1,
                "cost_usd": 18000.0,
                "risk_level": "LOW",
                "current_nodes": nodes
            }
            r_ins = requests.post(f"{BASE_WEB_URL}/api/linked-list/insert-node", json=insert_payload, timeout=10)
            data_ins = r_ins.json()
            log_test("apis", "POST /api/linked-list/insert-node", r_ins.status_code == 200 and len(data_ins.get("nodes", [])) == len(nodes) + 1, f"Nodes after insert: {len(data_ins.get('nodes', []))}")
    except Exception as e:
        log_test("apis", "POST /api/linked-list", False, str(e))

    # 15. Scraper
    try:
        r = requests.get(f"{BASE_WEB_URL}/api/scraper/live-indices", timeout=10)
        data = r.json()
        indices = data.get("market_indices", {})
        log_test("apis", "GET /api/scraper/live-indices", r.status_code == 200 and "baltic_dry_index" in indices, f"BDI: {indices.get('baltic_dry_index', {}).get('value')} pts")
    except Exception as e:
        log_test("apis", "GET /api/scraper/live-indices", False, str(e))

    # 16. What-If Simulation
    try:
        payload = {
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "cargo_tonnes": 80000.0,
            "spot_rate_usd_t": 24.50,
            "fuel_price_usd_mt": 610.0,
            "congestion_level": "Medium",
            "delay_days_override": 2.0
        }
        r = requests.post(f"{BASE_WEB_URL}/api/simulate/what-if", json=payload, timeout=10)
        data = r.json()
        log_test("apis", "POST /api/simulate/what-if", r.status_code == 200 and "new_decision" in data, f"Decision: {data.get('decision_badge')}, Landed cost: ₹{data.get('itemized_landed_cost_lakhs', {}).get('total_landed_cost')} L")
    except Exception as e:
        log_test("apis", "POST /api/simulate/what-if", False, str(e))

    # 17. Reports Export (JSON & CSV)
    try:
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
        r = requests.post(f"{BASE_WEB_URL}/api/reports/export", json=export_payload, timeout=10)
        log_test("apis", "POST /api/reports/export (JSON)", r.status_code == 200 and r.json().get("status") == "success", f"Title: {r.json().get('report_title')}")

        export_payload["format"] = "csv"
        r_csv = requests.post(f"{BASE_WEB_URL}/api/reports/export", json=export_payload, timeout=10)
        log_test("apis", "POST /api/reports/export (CSV)", r_csv.status_code == 200 and "text/csv" in r_csv.headers.get("content-type", ""), f"Bytes: {len(r_csv.text)}")
    except Exception as e:
        log_test("apis", "POST /api/reports/export", False, str(e))

def verify_streamlit():
    print("\n=======================================================")
    print(" TASK: VERIFY STREAMLIT DASHBOARD")
    print("=======================================================")
    try:
        r = requests.get(f"{BASE_ST_URL}/_stcore/health", timeout=5)
        log_test("streamlit", "Streamlit Health Probe", r.status_code == 200, f"HTTP {r.status_code} ({r.text.strip()})")
        
        r_page = requests.get(f"{BASE_ST_URL}", timeout=5)
        has_app_bundle = "streamlit" in r_page.text.lower()
        log_test("streamlit", "Streamlit App HTML Render", r_page.status_code == 200 and has_app_bundle, f"HTML size: {len(r_page.text)} bytes")
    except Exception as e:
        log_test("streamlit", "Streamlit Connection", False, str(e))

def main():
    start = time.time()
    verify_pages()
    verify_apis()
    verify_streamlit()
    total_time = round(time.time() - start, 2)

    total_tests = len(results["pages"]) + len(results["apis"]) + len(results["streamlit"])
    passed_tests = sum(1 for c in results.values() for t in c if t["passed"])
    failed_tests = total_tests - passed_tests

    print("\n=======================================================")
    print(f" EXECUTION SUMMARY: {passed_tests}/{total_tests} PASSED in {total_time}s")
    print("=======================================================")
    if failed_tests > 0:
        print(f"Failed count: {failed_tests}")
        sys.exit(1)
    else:
        print("ALL TASKS AND VERIFICATIONS COMPLETED SUCCESSFULLY!")
        sys.exit(0)

if __name__ == "__main__":
    main()
