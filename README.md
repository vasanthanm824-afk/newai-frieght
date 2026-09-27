# 🚢 SmartVessel AI & Freight Forecasting Decision Center

An enterprise-grade, AI-powered maritime decision intelligence platform for dry-bulk shipping, charter strategy optimization, port infrastructure compliance, freight rate forecasting, and live vessel tracking.

---

## 🌟 Key Features

1. **AI Freight Rate Forecasting**:
   - Temporal Fusion Transformer (TFT) Regressor & Spatial Graph Neural Networks (GNN).
   - Multi-horizon forward predictions (7-day, 14-day, 30-day, 6-month) with 95% confidence bounds ($R^2 = 0.9818$).
2. **Port Compatibility & Feasibility Engine**:
   - Multi-point constraint checks across Beam, LOA, and Draft for all key Indian East Coast discharge ports (Paradip, Vizag, Gangavaram, Gopalpur, Dhamra, Sagar-Sandheads, Haldia).
3. **Contract Strategy & Market Entry Optimizer**:
   - Spot vs. Short-Term vs. Mid-Term vs. Long-Term charter cost valuation.
   - Decision intelligence triggers (`BOOK NOW`, `WAIT`, `HEDGE`).
   - Idle vessel scenario planning, backhaul opportunities, and repositioning analysis.
4. **Doubly Linked List Voyage Routing**:
   - $O(1)$ dynamic waypoint insertion, bunkering hub additions, and automated recalculation of transit durations and costs.
5. **Voyage Economics & Pro-Forma Billing**:
   - Itemized accounting of bunker fuel consumption (VLSFO/IFO380), vessel hire, port dues, and IMO decarbonization compliance levies.
6. **Live Market Scraping & Real-Time Telemetry**:
   - Live Baltic Dry Index (BDI, BCI, BPI, BSI) ingestion and live simulated vessel IoT telemetry (pitch, roll, speed, coordinates).

---

## 🏗️ Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic v2.
- **Machine Learning**: Scikit-Learn, XGBoost, PyTorch (optional), Pandas, NumPy.
- **Frontend 1 (Web Portal)**: HTML5, CSS3, Vanilla ES6 JavaScript, Three.js 3D Globe, Bootstrap.
- **Frontend 2 (Dashboard)**: Streamlit, Plotly, Altair.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: Version 3.11 (recommended) or 3.10+.
- **Git** (optional).

### 2. Automatic One-Click Launch (Windows)
Double-click [`run_app.bat`](run_app.bat) in the root folder.
It automatically:
1. Detects or creates a Python virtual environment (`.venv`).
2. Installs all required packages and dependencies.
3. Seeds the historical database (`smartvessel.db`) with 81,760 records if not already initialized.
4. Trains and generates the ML model artifacts (`freight_model.pkl`) if missing.
5. Starts the FastAPI server and opens `http://127.0.0.1:8000` in your default browser.

### 3. Manual Installation & Execution

#### Step 1: Create Virtual Environment
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Step 2: Install Required Dependencies
```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install streamlit plotly xgboost matplotlib lxml
```

#### Step 3: Seed Database & Train Model
```powershell
# 1. Seed database with 730 days of maritime trade records
python SmartVesselAI/ml/dataset/seed_data.py

# 2. Train the forecasting model
python train_model.py
```

#### Step 4: Run the Application
```powershell
# Option A: Run the unified launcher
python run_app.py

# Option B: Run the FastAPI Web Server (Port 8000)
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Option C: Run the Streamlit Decision Dashboard (Port 8501)
streamlit run app.py --server.port 8501
```

---

## 🌐 Live Web Access Endpoints

| Portal | URL | Description |
| :--- | :--- | :--- |
| **SmartVessel AI Web Suite** | `http://127.0.0.1:8000` | 14-page interactive maritime web application. |
| **Interactive API Documentation** | `http://127.0.0.1:8000/docs` | Swagger OpenAPI UI to test all backend endpoints. |
| **Streamlit Decision Center** | `http://127.0.0.1:8501` | Full-screen 11-tab glassmorphic analytics dashboard. |

---

## 📡 REST API Modules

- `POST /api/process`: Unified end-to-end processing pipeline.
- `POST /api/forecast/predict`: Multi-month rate predictions with confidence intervals.
- `POST /api/contracts/compare`: Spot vs. Term charter cost valuations.
- `POST /api/contracts/benchmark`: Multi-scenario sensitivity comparison.
- `POST /api/voyage/cost`: Single-voyage landed economics.
- `POST /api/voyage/billing`: Pro-forma invoice and itemized charge statements.
- `POST /api/risk/alerts`: Multi-factor weather and congestion risk alerts.
- `POST /api/risk/evaluate-date`: 5-day alternative dispatch date generator.
- `POST /api/linked-list/build-route`: Doubly linked list route generation.
- `POST /api/reports/export`: Automated shipment reports in CSV or JSON.
- `GET /api/scraper/live-indices`: Real-time Baltic Dry indices.