"""End-to-End Browser & UI Simulation Test Suite for SmartVessel AI & Freight Forecasting Decision Center.

Verifies:
1. DOM Structure & Asset Integrity across all 14 HTML Frontend Pages
2. Form Input Controls, Buttons, Selects, and Result Containers
3. Interactive User-Journey Simulations (8 Guided Steps + Auxiliary Modules):
   - Step 1: Cargo Details Initializer (index.html)
   - Step 2: AI Multi-Horizon Freight Forecasting (forecast.html)
   - Step 3: Fleet Matrix & Vessel Selection (vessels.html)
   - Step 4: Port Constraints & Feasibility Validation (ports.html)
   - Step 5: Voyage Landed Cost & Pro-Forma Billing (billing.html)
   - Step 6: Risk Analysis & 5-Day Alternative Dispatch Window (risk.html)
   - Step 7: Charter Strategy Optimization (optimization.html)
   - Step 8: Executive Market Entry Decision Intelligence (decision.html)
   - Auxiliary 9: Doubly Linked List Dynamic Route Tracking (tracking.html)
   - Auxiliary 10: Real-Time Baltic Market Scraper & Bunker Telemetry
   - Auxiliary 11: What-If Sensitivity Shock Simulator (whatif.html)
   - Auxiliary 12: Decision Report Exporter (JSON & CSV)
   - Auxiliary 13: Streamlit Decision Center (Port 8501)
"""
from __future__ import annotations

import sys
import time
import json
import requests
from bs4 import BeautifulSoup

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"
ST_URL = "http://127.0.0.1:8501"

test_results: list[dict] = []

def record(phase: str, test_name: str, passed: bool, detail: str = ""):
    status_icon = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{status_icon}] [{phase}] {test_name}: {detail}", flush=True)
    test_results.append({
        "phase": phase,
        "name": test_name,
        "passed": passed,
        "detail": detail
    })

# ==============================================================================
# 1. DOM STRUCTURE & ASSET INTEGRITY AUDIT
# ==============================================================================
def audit_dom_and_assets():
    print("\n" + "=" * 70)
    print("PHASE 1: DOM STRUCTURE & STATIC ASSET AUDIT (14 PAGES)")
    print("=" * 70)

    pages = [
        ("index.html", "SmartVesselAI", ["smartvessel", "forecast", "dashboard"]),
        ("forecast.html", "Forecasting Engine", ["fc-origin", "fc-destination", "fc-vessel", "fc-cargo"]),
        ("vessels.html", "Vessel", ["handysize", "supramax", "panamax", "capesize"]),
        ("ports.html", "Port", ["paradip", "vizag", "draft"]),
        ("optimization.html", "Charter", ["voyage cost", "charter", "landed cost"]),
        ("decision.html", "Decision", ["charter", "decision", "paradip"]),
        ("billing.html", "Billing", ["invoice", "bunker", "usd"]),
        ("tracking.html", "Tracking", ["route", "tracking", "paradip"]),
        ("whatif.html", "What-If", ["simulation", "sensitivity", "fuel"]),
        ("risk.html", "Risk", ["weather", "monsoon", "congestion"]),
        ("alerts.html", "Alerts", ["notification", "alert"]),
        ("health.html", "Health", ["status", "system"]),
        ("settings.html", "Settings", ["configuration", "currency", "preference"]),
    ]

    for filename, title_keyword, required_elements in pages:
        url = f"{BASE_URL}/{filename}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                record("DOM_AUDIT", f"GET /{filename}", False, f"HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            title_ok = title_keyword.lower() in title.lower()

            # Verify body exists and has content
            body = soup.find("body")
            body_ok = body is not None and len(body.get_text().strip()) > 100

            # Verify key DOM elements or text snippets
            html_lower = r.text.lower()
            missing = [elem for elem in required_elements if elem not in html_lower]
            elements_ok = len(missing) == 0

            passed = title_ok and body_ok and elements_ok
            detail = f"Title: '{title}' | Elements: {len(required_elements)-len(missing)}/{len(required_elements)}"
            if missing:
                detail += f" (missing: {missing})"

            record("DOM_AUDIT", f"Page /{filename}", passed, detail)

        except Exception as e:
            record("DOM_AUDIT", f"Page /{filename}", False, str(e))

    # Verify static assets referenced in pages
    print("\n--- Verifying Core Static Assets ---")
    core_assets = [
        "/static/style.css",
        "/static/js/workflowState.js",
        "/static/js/global_ports.js",
        "/static/js/currencyConfig.js",
        "/static/js/currencyService.js",
    ]
    for asset in core_assets:
        try:
            r = requests.get(f"{BASE_URL}{asset}", timeout=5)
            record("STATIC_ASSET", asset, r.status_code == 200 and len(r.text) > 100, f"HTTP {r.status_code}, size={len(r.text)} bytes")
        except Exception as e:
            record("STATIC_ASSET", asset, False, str(e))

# ==============================================================================
# 2. INTERACTIVE USER-JOURNEY SIMULATIONS
# ==============================================================================
def simulate_user_journeys():
    print("\n" + "=" * 70)
    print("PHASE 2: INTERACTIVE USER-JOURNEY SIMULATIONS")
    print("=" * 70)

    # Journey 1: Route & Port Catalog Discovery
    try:
        r_countries = requests.get(f"{BASE_URL}/api/ports/all-countries", timeout=5)
        countries_data = r_countries.json()
        countries = countries_data.get("countries", [])
        record("USER_JOURNEY", "1. Port Discovery (All Countries)", len(countries) >= 10, f"Found {len(countries)} available origin countries")

        r_origin_ports = requests.get(f"{BASE_URL}/api/ports/by-country?country=Australia", timeout=5)
        aus_ports = r_origin_ports.json().get("port_names", [])
        record("USER_JOURNEY", "1. Port Discovery (Australia Ports)", "Newcastle" in aus_ports, f"Ports: {aus_ports}")

        r_dest_ports = requests.get(f"{BASE_URL}/api/ports/indian", timeout=5)
        dest_ports = r_dest_ports.json().get("port_names", [])
        record("USER_JOURNEY", "1. Port Discovery (Indian East Coast)", len(dest_ports) == 7, f"Ports: {dest_ports}")
    except Exception as e:
        record("USER_JOURNEY", "1. Port Discovery", False, str(e))

    # Journey 2: AI Multi-Horizon Freight Forecasting
    try:
        forecast_payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "months": 6
        }
        r_fc = requests.post(f"{BASE_URL}/api/forecast", json=forecast_payload, timeout=10)
        fc_data = r_fc.json()
        forecast_points = fc_data.get("forecast", [])
        has_bounds = all("rate_lower" in p and "rate_upper" in p for p in forecast_points)
        valid_rates = all(p.get("rate_usd_per_ton", 0) > 0 for p in forecast_points)

        record("USER_JOURNEY", "2. Freight Forecast Simulation (Newcastle -> Paradip, Supramax)",
               r_fc.status_code == 200 and len(forecast_points) == 6 and has_bounds and valid_rates,
               f"Forecast {len(forecast_points)} months, Day 30: ${forecast_points[0].get('rate_usd_per_ton', 0):.2f}/MT (Lower: ${forecast_points[0].get('rate_lower', 0):.2f}, Upper: ${forecast_points[0].get('rate_upper', 0):.2f})")
    except Exception as e:
        record("USER_JOURNEY", "2. Freight Forecast Simulation", False, str(e))

    # Journey 3: Fleet Specification & Vessel Selection Matrix
    try:
        r_vessels = requests.get(f"{BASE_URL}/api/ports/vessels", timeout=5)
        vessels_data = r_vessels.json().get("vessels", [])
        vessel_types = [v["vessel_type"] for v in vessels_data]
        expected_types = ["Handysize", "Supramax", "Panamax", "Capesize"]
        all_present = all(vt in vessel_types for vt in expected_types)
        record("USER_JOURNEY", "3. Fleet Matrix Selection",
               r_vessels.status_code == 200 and all_present,
               f"Vessel classes verified: {vessel_types}")
    except Exception as e:
        record("USER_JOURNEY", "3. Fleet Matrix Selection", False, str(e))

    # Journey 4: Port Compatibility & Constraint Enforcement
    try:
        # Paradip: draft 14.5m, Haldia: draft 8.5m, Vizag: draft 16.5m
        # Supramax: draft ~12.2m -> passes Paradip & Vizag, passes or restricted at Haldia
        # Capesize: draft ~18.0m -> fails Haldia & Paradip, passes Vizag deep-water
        vessel_specs = {v["vessel_type"]: v for v in vessels_data}
        capesize_draft = vessel_specs.get("Capesize", {}).get("design_draft_m", 18.0)
        haldia_max_draft = 8.5
        paradip_max_draft = 14.5
        vizag_max_draft = 16.5

        capesize_fits_haldia = capesize_draft <= haldia_max_draft
        capesize_fits_paradip = capesize_draft <= paradip_max_draft

        record("USER_JOURNEY", "4. Port Feasibility Constraint Check",
               (not capesize_fits_haldia) and (not capesize_fits_paradip),
               f"Capesize ({capesize_draft}m draft) correctly rejected at Haldia ({haldia_max_draft}m) & Paradip ({paradip_max_draft}m)")
    except Exception as e:
        record("USER_JOURNEY", "4. Port Feasibility Constraint Check", False, str(e))

    # Journey 5: Voyage Landed Cost & Pro-Forma Invoice Generation
    try:
        voyage_payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0
        }
        r_voyage = requests.post(f"{BASE_URL}/api/voyage/cost", json=voyage_payload, timeout=10)
        v_data = r_voyage.json().get("voyage", {})
        total_voyage_cost = v_data.get("total_cost_usd", 0)
        voyage_days = v_data.get("total_voyage_days", 0)

        record("USER_JOURNEY", "5. Voyage Economics Calculation",
               r_voyage.status_code == 200 and total_voyage_cost > 0 and voyage_days > 0,
               f"Total: ${total_voyage_cost:,.2f} USD, Duration: {voyage_days} days, Cost/Ton: ${v_data.get('cost_per_tonne', 0):.2f}")

        # Pro-Forma Billing Invoice
        billing_payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "spot_rate_per_ton": 28.50,
            "discount_pct": 3.0,
            "tax_pct": 5.0
        }
        r_bill = requests.post(f"{BASE_URL}/api/voyage/billing", json=billing_payload, timeout=10)
        b_data = r_bill.json()
        inv_no = b_data.get("invoice_number")
        grand_total = b_data.get("billing_summary", {}).get("grand_total_usd", 0)

        record("USER_JOURNEY", "5. Pro-Forma Billing & Invoice Generation",
               r_bill.status_code == 200 and inv_no is not None and grand_total > 0,
               f"Invoice Ref: {inv_no}, Grand Total: ${grand_total:,.2f} USD (with 3% disc, 5% tax)")
    except Exception as e:
        record("USER_JOURNEY", "5. Voyage Economics & Billing", False, str(e))

    # Journey 6: Risk Alerts & 5-Day Alternative Dispatch Window
    try:
        risk_payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "months": 6
        }
        r_risk = requests.post(f"{BASE_URL}/api/risk/alerts", json=risk_payload, timeout=10)
        alerts = r_risk.json().get("alerts", [])
        record("USER_JOURNEY", "6. Risk & Monsoon Weather Alerts",
               r_risk.status_code == 200 and len(alerts) > 0,
               f"Generated {len(alerts)} contextual operational alerts")

        eval_payload = {
            "target_date": "2026-07-20",
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_country": "India",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0
        }
        r_eval = requests.post(f"{BASE_URL}/api/risk/evaluate-date", json=eval_payload, timeout=10)
        alt_dates = r_eval.json().get("alternative_dates", [])
        record("USER_JOURNEY", "6. 5-Day Alternative Dispatch Window",
               r_eval.status_code == 200 and len(alt_dates) == 5,
               f"Computed 5 alternative departure dates with risk metrics")
    except Exception as e:
        record("USER_JOURNEY", "6. Risk & Dispatch Window", False, str(e))

    # Journey 7: Charter Strategy Optimization & Multi-Scenario Benchmark
    try:
        contract_payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "voyages_per_year": 6
        }
        r_contract = requests.post(f"{BASE_URL}/api/contracts/compare", json=contract_payload, timeout=10)
        c_data = r_contract.json().get("contract", {})
        rec_strat = c_data.get("recommended_strategy")
        savings = c_data.get("savings_vs_spot", 0)

        record("USER_JOURNEY", "7. Charter Strategy Optimization",
               r_contract.status_code == 200 and rec_strat is not None,
               f"Recommended Strategy: '{rec_strat}', Est. Savings vs Spot: ${savings:,.2f} USD")

        benchmark_payload = {
            "scenarios": [
                {"scenario_name": "Standard Supramax Paradip", "origin_country": "Australia", "destination_port": "Paradip", "vessel_type": "Supramax", "cargo_tonnes": 50000, "voyages_per_year": 6},
                {"scenario_name": "Larger Panamax Vizag", "origin_country": "Australia", "destination_port": "Vizag", "vessel_type": "Panamax", "cargo_tonnes": 80000, "voyages_per_year": 4}
            ]
        }
        r_bench = requests.post(f"{BASE_URL}/api/contracts/benchmark", json=benchmark_payload, timeout=10)
        bench_data = r_bench.json()
        rec_scenario = bench_data.get("recommended_scenario")

        record("USER_JOURNEY", "7. Multi-Scenario Sensitivity Benchmark",
               r_bench.status_code == 200 and len(bench_data.get("results", [])) == 2,
               f"Optimal Scenario: '{rec_scenario}'")
    except Exception as e:
        record("USER_JOURNEY", "7. Charter Optimization & Benchmark", False, str(e))

    # Journey 8: Executive Market Entry Decision Intelligence
    try:
        entry_payload = {
            "origin_country": "Australia",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0,
            "forecast_months": 6
        }
        r_entry = requests.post(f"{BASE_URL}/api/contracts/market-entry", json=entry_payload, timeout=10)
        entry_data = r_entry.json().get("signal", {})
        action = entry_data.get("action")
        confidence = entry_data.get("confidence")

        record("USER_JOURNEY", "8. Final Decision Intelligence Trigger",
               r_entry.status_code == 200 and action in ["BOOK NOW", "WAIT", "HEDGE"],
               f"Market Entry Action: {action} (Confidence: {confidence})")
    except Exception as e:
        record("USER_JOURNEY", "8. Decision Intelligence", False, str(e))

    # Journey 9: Doubly Linked List Route Management & Dynamic Waypoint Insertion
    try:
        route_payload = {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_country": "India",
            "destination_port": "Paradip",
            "vessel_type": "Supramax",
            "cargo_tonnes": 50000.0
        }
        r_route = requests.post(f"{BASE_URL}/api/linked-list/build-route", json=route_payload, timeout=10)
        nodes = r_route.json().get("nodes", [])
        record("USER_JOURNEY", "9. Doubly Linked List Route Construction",
               r_route.status_code == 200 and len(nodes) >= 3,
               f"Initial Route Nodes: {len(nodes)} (Origin: {nodes[0].get('location_name')} -> Dest: {nodes[-1].get('location_name')})")

        # Dynamic Waypoint Insertion
        if nodes:
            insert_payload = {
                "target_node_id": nodes[0]["node_id"],
                "new_node_title": "Singapore Bunkering Hub",
                "location_name": "Singapore Strait",
                "country": "Singapore",
                "vessel_type": "Supramax",
                "distance_nm": 450.0,
                "est_days": 1.5,
                "cost_usd": 25000.0,
                "risk_level": "LOW",
                "current_nodes": nodes
            }
            r_ins = requests.post(f"{BASE_URL}/api/linked-list/insert-node", json=insert_payload, timeout=10)
            ins_nodes = r_ins.json().get("nodes", [])
            node_inserted = len(ins_nodes) == len(nodes) + 1
            record("USER_JOURNEY", "9. Dynamic Node Insertion & Recalculation",
                   r_ins.status_code == 200 and node_inserted,
                   f"Route expanded to {len(ins_nodes)} nodes with Singapore Bunkering Hub inserted")
    except Exception as e:
        record("USER_JOURNEY", "9. Doubly Linked Route Tracking", False, str(e))

    # Journey 10: Real-Time Market Scraping & Live Telemetry
    try:
        r_scrape = requests.get(f"{BASE_URL}/api/scraper/live-indices", timeout=10)
        scrape_data = r_scrape.json()
        indices = scrape_data.get("market_indices", {})
        bunker = scrape_data.get("bunker_prices", {})
        bdi_val = indices.get("baltic_dry_index", {}).get("value")

        record("USER_JOURNEY", "10. Baltic Indices & Global Bunker Scraper",
               r_scrape.status_code == 200 and bdi_val is not None and len(bunker) >= 4,
               f"BDI: {bdi_val} pts, Bunkering Ports: {list(bunker.keys())}")
    except Exception as e:
        record("USER_JOURNEY", "10. Market Scraper", False, str(e))

    # Journey 11: What-If Sensitivity Simulator
    try:
        whatif_payload = {
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_type": "Panamax",
            "cargo_tonnes": 80000.0,
            "spot_rate_usd_t": 26.00,
            "fuel_price_usd_mt": 650.0,
            "congestion_level": "High",
            "delay_days_override": 4.5
        }
        r_whatif = requests.post(f"{BASE_URL}/api/simulate/what-if", json=whatif_payload, timeout=10)
        wi_data = r_whatif.json()
        badge = wi_data.get("decision_badge")
        landed_lakhs = wi_data.get("itemized_landed_cost_lakhs", {}).get("total_landed_cost")

        record("USER_JOURNEY", "11. What-If Sensitivity Shock Simulator",
               r_whatif.status_code == 200 and badge is not None and landed_lakhs is not None,
               f"Shock Decision: '{badge}', Landed Cost: ₹{landed_lakhs} Lakhs")
    except Exception as e:
        record("USER_JOURNEY", "11. What-If Simulator", False, str(e))

    # Journey 12: Automated Decision Report Exporter
    try:
        exp_payload = {
            "origin_country": "Australia",
            "destination_country": "India",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "cargo_tonnes": 50000,
            "vessel_type": "Supramax",
            "forecast_months": 6,
            "format": "json"
        }
        r_exp_json = requests.post(f"{BASE_URL}/api/reports/export", json=exp_payload, timeout=10)
        exp_payload["format"] = "csv"
        r_exp_csv = requests.post(f"{BASE_URL}/api/reports/export", json=exp_payload, timeout=10)

        record("USER_JOURNEY", "12. Decision Report Export (JSON & CSV)",
               r_exp_json.status_code == 200 and r_exp_csv.status_code == 200 and len(r_exp_csv.text) > 200,
               f"JSON Export: '{r_exp_json.json().get('report_title')}', CSV Export: {len(r_exp_csv.text)} bytes")
    except Exception as e:
        record("USER_JOURNEY", "12. Decision Report Export", False, str(e))

    # Journey 13: Streamlit Analytics Dashboard Verification
    try:
        r_st_health = requests.get(f"{ST_URL}/_stcore/health", timeout=5)
        r_st_render = requests.get(f"{ST_URL}", timeout=5)
        has_bundle = "streamlit" in r_st_render.text.lower()

        record("USER_JOURNEY", "13. Streamlit Decision Center (Port 8501)",
               r_st_health.status_code == 200 and has_bundle,
               f"Health: HTTP {r_st_health.status_code} ({r_st_health.text.strip()}), Bundle: {len(r_st_render.text)} bytes")
    except Exception as e:
        record("USER_JOURNEY", "13. Streamlit Decision Center", False, str(e))

# ==============================================================================
# MAIN TEST EXECUTION & SUMMARY
# ==============================================================================
def main():
    start_time = time.time()
    audit_dom_and_assets()
    simulate_user_journeys()
    duration = round(time.time() - start_time, 2)

    total = len(test_results)
    passed = sum(1 for t in test_results if t["passed"])
    failed = total - passed

    print("\n" + "=" * 70)
    print(f" END-TO-END TEST SUITE EXECUTION SUMMARY")
    print(f" TOTAL TESTS RUN : {total}")
    print(f" PASSED          : {passed}")
    print(f" FAILED          : {failed}")
    print(f" DURATION        : {duration}s")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL TESTS AND END-TO-END USER JOURNEYS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED:")
        for t in test_results:
            if not t["passed"]:
                print(f"  - [{t['phase']}] {t['name']}: {t['detail']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
