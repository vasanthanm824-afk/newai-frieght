import requests
import json
import sys
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def verify_fastapi():
    print("=" * 60)
    print("VERIFYING FASTAPI & WEB FRONTEND (http://127.0.0.1:8000)")
    print("=" * 60)
    
    # 1. Check Root / index.html
    r = requests.get("http://127.0.0.1:8000/")
    print(f"GET / -> Status Code: {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    
    title = soup.title.string.strip() if soup.title else "None"
    print(f"Page Title: {title}")
    
    brand = soup.find(class_="smartvessel-brand")
    brand_text = brand.get_text(separator=" ", strip=True) if brand else "None"
    print(f"Brand: {brand_text}")
    
    govt_brand = soup.find(class_="govt-brand-box")
    govt_brand_text = govt_brand.get_text(separator=" ", strip=True) if govt_brand else "None"
    print(f"Header Government Emblem/Text: {govt_brand_text}")
    
    # Navigation Links
    print("\n--- Header Navigation Links ---")
    nav_links = soup.select(".header-top-nav a")
    for link in nav_links:
        print(f"  Header Nav: '{link.get_text(strip=True)}' -> href='{link.get('href')}'")
        
    print("\n--- Sidebar Navigation Links ---")
    sidebar_links = soup.select(".sidebar-menu-group a")
    for link in sidebar_links:
        print(f"  Sidebar Nav: '{link.get_text(strip=True)}' -> href='{link.get('href')}'")
        
    # Key Components on Index
    print("\n--- Key Components on Dashboard (index.html) ---")
    hero_title = soup.select_one(".hero-main-title")
    print(f"  Hero Title: {hero_title.get_text(strip=True) if hero_title else 'None'}")
    
    kpi_cards = soup.select(".kpi-card-ref")
    print(f"  KPI Summary Cards Count: {len(kpi_cards)}")
    for card in kpi_cards:
        label = card.select_one(".kpi-label")
        val = card.select_one(".kpi-val")
        print(f"    - {label.get_text(strip=True) if label else ''}: {val.get_text(strip=True) if val else ''}")
        
    charts = soup.select("#plotly-trend-chart, #global-trade-map, #cargo-dist-chart")
    print(f"  Plotly/Map Containers: {[c.get('id') for c in charts]}")
    
    # 2. Check forecast.html
    print("\n" + "=" * 60)
    print("VERIFYING FORECAST PAGE (http://127.0.0.1:8000/forecast.html)")
    print("=" * 60)
    rf = requests.get("http://127.0.0.1:8000/forecast.html")
    print(f"GET /forecast.html -> Status Code: {rf.status_code}")
    soup_fc = BeautifulSoup(rf.text, "html.parser")
    print(f"Forecast Title: {soup_fc.title.string.strip() if soup_fc.title else 'None'}")
    
    form = soup_fc.select_one("#forecast-form")
    print(f"Forecast Form Present: {form is not None}")
    if form:
        origin_opts = [o.get_text(strip=True) for o in soup_fc.select("#fc-origin option")]
        dest_opts = [o.get_text(strip=True) for o in soup_fc.select("#fc-destination option")]
        vessel_opts = [o.get_text(strip=True) for o in soup_fc.select("#fc-vessel option")]
        cargo_val = soup_fc.select_one("#fc-cargo")
        print(f"  Origin Options: {origin_opts}")
        print(f"  Destination Options: {dest_opts}")
        print(f"  Vessel Options: {vessel_opts}")
        print(f"  Cargo Default: {cargo_val.get('value') if cargo_val else 'None'}")
        
    submit_btn = soup_fc.select_one("#forecast-form button[type='submit']")
    print(f"  Submit Button: {submit_btn.get_text(strip=True) if submit_btn else 'None'}")
    
    # 3. Test Forecast API endpoint used by forecast.html
    print("\n--- Testing Forecast Prediction API (/api/forecast/predict) ---")
    payload = {
        "origin_country": "Australia",
        "destination_port": "Paradip",
        "vessel_type": "Panamax",
        "cargo_quantity_mt": 80000
    }
    r_api = requests.post("http://127.0.0.1:8000/api/forecast/predict", json=payload)
    print(f"POST /api/forecast/predict -> Status Code: {r_api.status_code}")
    if r_api.status_code == 200:
        data = r_api.json()
        print(f"  Current Spot Rate: {data.get('current_spot_rate')}")
        print(f"  Overall Trend: {data.get('overall_trend')} ({data.get('trend_percentage')}%)")
        print(f"  AI Confidence: {data.get('ai_confidence_pct')}%")
        print(f"  Horizons returned: {list(data.get('horizons', {}).keys())}")
        for h, v in data.get('horizons', {}).items():
            print(f"    - {h}: Predicted={v.get('predicted_rate')}, Bounds=[{v.get('lower_bound')}, {v.get('upper_bound')}]")
            
    # 4. Check All Linked Pages in Navigation
    print("\n--- Verifying All Navigation Target Pages ---")
    pages = [
        "index.html", "forecast.html", "optimization.html", "vessels.html",
        "ports.html", "risk.html", "decision.html", "billing.html",
        "settings.html", "alerts.html", "tracking.html", "whatif.html", "health.html"
    ]
    for p in pages:
        res = requests.get(f"http://127.0.0.1:8000/{p}")
        p_soup = BeautifulSoup(res.text, "html.parser")
        p_title = p_soup.title.string.strip() if p_soup.title else "No Title"
        print(f"  /{p:18} -> Status {res.status_code}, Title: {p_title}")

def verify_streamlit():
    print("\n" + "=" * 60)
    print("VERIFYING STREAMLIT DASHBOARD (http://127.0.0.1:8501)")
    print("=" * 60)
    
    # 1. Health check
    r_health = requests.get("http://127.0.0.1:8501/_stcore/health")
    print(f"GET /_stcore/health -> Status: {r_health.status_code}, Content: {r_health.text.strip()}")
    
    # 2. Main app HTML
    r_main = requests.get("http://127.0.0.1:8501/")
    print(f"GET / -> Status: {r_main.status_code}")
    st_soup = BeautifulSoup(r_main.text, "html.parser")
    print(f"Streamlit Title: {st_soup.title.string.strip() if st_soup.title else 'None'}")
    
    # Check static bundles
    scripts = [s.get('src') for s in st_soup.find_all('script') if s.get('src')]
    print(f"Streamlit JS Bundles Loaded: {len(scripts)} scripts found")
    all_scripts_ok = True
    for s in scripts:
        if s.startswith('/'):
            bundle_url = f"http://127.0.0.1:8501{s}"
            rb = requests.get(bundle_url)
            if rb.status_code != 200:
                print(f"  Warning: script {s} returned {rb.status_code}")
                all_scripts_ok = False
    if all_scripts_ok:
        print("  All Streamlit frontend static assets loaded successfully (200 OK).")

    # 3. Test api_client.py connecting to FastAPI backend
    print("\n--- Testing Streamlit FreightAPIClient -> Backend Integration ---")
    from api_client import FreightAPIClient
    client = FreightAPIClient(base_url="http://127.0.0.1:8000")
    health = client.check_health()
    print(f"  API Client Health: {health}")
    
    countries = client.get_all_countries()
    print(f"  API Client Countries count: {len(countries) if countries else 0}")
    
    vessels = client.get_vessel_catalog()
    print(f"  API Client Vessels count: {len(vessels) if vessels else 0}")
    
    fc_df = client.get_forecast(
        origin_country="Australia",
        destination_port="Paradip",
        vessel_type="Panamax",
        cargo_tonnes=75000,
        months=6
    )
    print(f"  API Client Forecast: DataFrame shape={fc_df.shape if not fc_df.empty else 'empty'}")

if __name__ == "__main__":
    verify_fastapi()
    verify_streamlit()
