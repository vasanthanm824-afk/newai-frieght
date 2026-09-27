import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def test_page(path, expected_snippets):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            for snippet in expected_snippets:
                if snippet not in content:
                    print(f"FAILED: {path} missing snippet: '{snippet}'")
                    return False
            print(f"PASS: {path} (HTTP {resp.status}) - All {len(expected_snippets)} snippets present")
            return True
    except Exception as e:
        print(f"ERROR fetching {path}: {e}")
        return False

def test_api_post(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            print(f"PASS: POST {path} (HTTP {resp.status}) - Response keys: {list(res_json.keys()) if isinstance(res_json, dict) else 'List'}")
            return True
    except Exception as e:
        print(f"ERROR calling {path}: {e}")
        return False

def main():
    print("=== STARTING FULL E2E LOCALHOST VERIFICATION ===")
    
    pages = [
        ("/", [
            "START NEW CARGO ANALYSIS",
            "workflowState.js",
            "renderTransactionHeader(1)",
            "Cargo Details",
            "form-guided-input"
        ]),
        ("/static/js/workflowState.js", [
            "SmartVesselWorkflow",
            "getSession",
            "saveSession",
            "invalidateDownstream",
            "renderTransactionHeader",
            "renderTransactionFooter"
        ]),
        ("/forecast.html", [
            "STEP 2 OF 8",
            "workflowState.js",
            "renderTransactionHeader(2)",
            "renderTransactionFooter(2"
        ]),
        ("/vessels.html", [
            "STEP 3 OF 8",
            "workflowState.js",
            "renderTransactionHeader(3)",
            "renderTransactionFooter(3"
        ]),
        ("/ports.html", [
            "STEP 4 OF 8",
            "workflowState.js",
            "renderTransactionHeader(4)",
            "renderTransactionFooter(4"
        ]),
        ("/billing.html", [
            "STEP 5 OF 8",
            "workflowState.js",
            "renderTransactionHeader(5)",
            "renderTransactionFooter(5"
        ]),
        ("/risk.html", [
            "STEP 6 OF 8",
            "workflowState.js",
            "renderTransactionHeader(6)",
            "renderTransactionFooter(6"
        ]),
        ("/optimization.html", [
            "STEP 7 OF 8",
            "workflowState.js",
            "renderTransactionHeader(7)",
            "renderTransactionFooter(7"
        ]),
        ("/decision.html", [
            "STEP 8 OF 8",
            "workflowState.js",
            "renderTransactionHeader(8)",
            "Export PDF",
            "Export CSV",
            "Export JSON",
            "START NEW ANALYSIS"
        ])
    ]
    
    all_pages_pass = True
    for path, snippets in pages:
        if not test_page(path, snippets):
            all_pages_pass = False
            
    print("\n--- TESTING API ENDPOINTS ---")
    apis = [
        ("/api/forecast", {
            "origin_country": "Australia",
            "origin_port": "Newcastle",
            "destination_port": "Paradip",
            "cargo_type": "Coking Coal",
            "cargo_quantity": 75000,
            "vessel_type": "Panamax"
        }),
        ("/api/compatibility", {
            "vessel_name": "Panamax Leader",
            "draft_m": 13.2,
            "loa_m": 225.0,
            "beam_m": 32.2,
            "dwt": 75000,
            "origin_port": "Newcastle",
            "destination_port": "Paradip"
        }),
        ("/api/voyage/billing", {
            "freight_rate_pmt": 18.5,
            "cargo_quantity_mt": 75000,
            "bunker_fuel_cost": 125000,
            "port_dues": 45000,
            "imo_decarb_levy": 15000,
            "tax_pct": 5.0
        }),
        ("/api/risk/center", {
            "route": "Australia -> Paradip",
            "vessel_type": "Panamax"
        }),
        ("/api/optimize", {
            "spot_rate": 18.5,
            "time_charter_rate": 17.2,
            "coa_rate": 16.8,
            "quantity_mt": 75000
        })
    ]
    
    all_apis_pass = True
    for path, payload in apis:
        if not test_api_post(path, payload):
            all_apis_pass = False
            
    if all_pages_pass and all_apis_pass:
        print("\n=== ALL E2E VERIFICATIONS PASSED SUCCESSFULLY ===")
        sys.exit(0)
    else:
        print("\n=== E2E VERIFICATION FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
