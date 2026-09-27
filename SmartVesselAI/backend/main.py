import os
import sys
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

SMARTVESSEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if sys.path[0] != SMARTVESSEL_DIR:
    sys.path.insert(0, SMARTVESSEL_DIR)

try:
    from backend.database import engine, Base, get_db
    from backend.models.db_models import FreightRate, Vessel, Port, Cargo, Telemetry
    from backend.schemas import (
        ForecastRequest, ForecastResponse,
        CompatibilityRequest, CompatibilityResponse,
        OptimizationRequest, OptimizationResponse,
        TelemetryCreate, TelemetryResponse,
        BillRequest, BillResponse
    )
    from ml.predict import FreightPredictor
    from optimization.charter_optimizer import CharterOptimizer
except ModuleNotFoundError:
    from .database import engine, Base, get_db
    from .models.db_models import FreightRate, Vessel, Port, Cargo, Telemetry
    from .schemas import (
        ForecastRequest, ForecastResponse,
        CompatibilityRequest, CompatibilityResponse,
        OptimizationRequest, OptimizationResponse,
        TelemetryCreate, TelemetryResponse,
        BillRequest, BillResponse
    )
    from SmartVesselAI.ml.predict import FreightPredictor
    from SmartVesselAI.optimization.charter_optimizer import CharterOptimizer
import random

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartVesselAI API Engine",
    description="Maritime Freight Rate Forecasting, Vessel Selection, Port Compatibility, and Charter Optimization Platform",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
predictor = FreightPredictor()
optimizer = CharterOptimizer()

@app.get("/api/health")
def health_check():
    return {"status": "ONLINE", "system": "SmartVesselAI Engine v1.0.0"}

from ml.train import train_freight_models

# Module 2: Freight Forecasting API
@app.post("/api/forecast", response_model=ForecastResponse)
def get_freight_forecast(req: ForecastRequest):
    res = predictor.predict(req.origin, req.destination, req.vessel_type)
    return res

@app.post("/api/train")
def trigger_training():
    artifact = train_freight_models()
    if not artifact:
        raise HTTPException(status_code=500, detail="Model training failed.")
    predictor._load_model() # Reload trained model into memory
    return {
        "status": "SUCCESS",
        "message": f"Successfully trained XGBoost models on {artifact['total_records']:,} historical global freight records.",
        "metrics": artifact['metrics'],
        "total_records": artifact['total_records'],
        "trained_at": artifact['trained_at']
    }

@app.get("/api/train/metrics")
def get_model_metrics():
    if predictor.artifact:
        return {
            "trained": True,
            "metrics": predictor.artifact.get('metrics', {}),
            "total_records": predictor.artifact.get('total_records', 0),
            "trained_at": predictor.artifact.get('trained_at', 'N/A')
        }
    return {"trained": False, "message": "Model not yet trained."}

# Module 3 & 4: Vessels & Ports APIs
@app.get("/api/vessels")
def list_vessels(db: Session = Depends(get_db)):
    vessels = db.query(Vessel).all()
    return vessels

@app.get("/api/ports")
def list_ports(db: Session = Depends(get_db)):
    ports = db.query(Port).order_by(Port.country.asc(), Port.port_name.asc()).all()
    return ports

@app.get("/api/countries")
def list_countries(db: Session = Depends(get_db)):
    countries = db.query(Port.country).distinct().all()
    country_list = sorted([c[0] for c in countries if c[0]])
    return country_list

@app.post("/api/compatibility", response_model=CompatibilityResponse)
def check_compatibility(req: CompatibilityRequest, db: Session = Depends(get_db)):
    vessel = db.query(Vessel).filter(Vessel.vessel_name == req.vessel_name).first()
    if not vessel:
        vessel = db.query(Vessel).first()
    port = db.query(Port).filter(Port.port_name == req.port_name).first()
    if not port:
        port = db.query(Port).first()

    if not vessel or not port:
        raise HTTPException(status_code=404, detail="Vessel or Port not found.")

    res = optimizer.check_port_compatibility(vessel, port, req.cargo_tonnes)
    return res

# Module 5 & 6: Cost Calculation & Optimization Engine API
@app.post("/api/optimize", response_model=OptimizationResponse)
def optimize_charter(req: OptimizationRequest):
    res = optimizer.optimize(req.origin, req.destination, req.cargo_tonnes, req.commodity)
    return res

# Bill & Process Generation Endpoint
@app.post("/api/bill/generate", response_model=BillResponse)
def generate_client_bill(req: BillRequest, db: Session = Depends(get_db)):
    bill_id = f"BILL-2026-{random.randint(1000, 9999)}"
    
    fc = predictor.predict(req.origin, req.destination, req.vessel_type)
    opt = optimizer.optimize(req.origin, req.destination, req.cargo_tonnes, req.commodity)
    
    rec_vessel_name = opt["recommended_vessel"]
    vessel = db.query(Vessel).filter(Vessel.vessel_name == rec_vessel_name).first()
    if not vessel:
        vessel = db.query(Vessel).first()
        
    port = db.query(Port).filter(Port.port_name == req.destination).first()
    if not port:
        port = db.query(Port).first()
        
    compat = optimizer.check_port_compatibility(vessel, port, req.cargo_tonnes) if (vessel and port) else {}
    best_opt = opt["all_options"][0] if opt["all_options"] else {}
    
    return {
        "bill_id": bill_id,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "client_summary": {
            "origin": req.origin,
            "destination": req.destination,
            "commodity": req.commodity,
            "cargo_tonnes": req.cargo_tonnes,
            "vessel_type_requested": req.vessel_type
        },
        "forecast_summary": {
            "current_rate": fc["current_rate"],
            "forecast_7d": fc["forecast_7d"],
            "forecast_14d": fc["forecast_14d"],
            "forecast_30d": fc["forecast_30d"],
            "trend": fc["trend"]
        },
        "recommended_vessel": {
            "vessel_name": vessel.vessel_name if vessel else "Panamax Explorer",
            "vessel_type": vessel.vessel_type if vessel else "Panamax",
            "capacity": vessel.capacity if vessel else 82000,
            "draft": vessel.draft if vessel else 13.8,
            "speed": vessel.speed if vessel else 13.5,
            "daily_charter_rate": vessel.daily_charter_rate if vessel else 14500
        },
        "port_compliance": compat,
        "itemized_costs": {
            "freight_cost": best_opt.get("freight_cost", 0.0),
            "fuel_cost": best_opt.get("fuel_cost", 0.0),
            "port_cost": best_opt.get("port_cost", 0.0),
            "waiting_cost": best_opt.get("waiting_cost", 0.0),
            "idle_cost": best_opt.get("idle_cost", 0.0),
            "risk_penalty": best_opt.get("risk_penalty", 0.0)
        },
        "total_bill_amount_lakhs": opt["estimated_total_cost"],
        "recommendation_action": opt["recommended_action"],
        "explanations": opt["explanation"]
    }

# Module 13: IoT Telemetry API
@app.post("/api/telemetry/stream")
def receive_telemetry(data: TelemetryCreate, db: Session = Depends(get_db)):
    entry = Telemetry(
        vessel_id=data.vessel_id,
        latitude=data.latitude,
        longitude=data.longitude,
        speed=data.speed,
        temperature=data.temperature,
        humidity=data.humidity,
        pitch=data.pitch,
        roll=data.roll,
        status=data.status
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "SUCCESS", "id": entry.id, "timestamp": str(entry.timestamp)}

@app.get("/api/telemetry/latest/{vessel_id}")
def get_latest_telemetry(vessel_id: str, db: Session = Depends(get_db)):
    entry = db.query(Telemetry).filter(Telemetry.vessel_id == vessel_id).order_by(Telemetry.id.desc()).first()
    if not entry:
        entry = db.query(Telemetry).order_by(Telemetry.id.desc()).first()
    if not entry:
        return {
            "vessel_id": vessel_id,
            "latitude": 11.62,
            "longitude": 92.72,
            "speed": 13.4,
            "temperature": 28.5,
            "humidity": 75.0,
            "pitch": 1.2,
            "roll": 2.1,
            "status": "IN_TRANSIT",
            "timestamp": "N/A"
        }
    return {
        "vessel_id": entry.vessel_id,
        "latitude": entry.latitude,
        "longitude": entry.longitude,
        "speed": entry.speed,
        "temperature": entry.temperature,
        "humidity": entry.humidity,
        "pitch": entry.pitch,
        "roll": entry.roll,
        "status": entry.status,
        "timestamp": str(entry.timestamp)
    }

# Mount Frontend Static Files
FRONTEND_DIR = os.path.abspath(os.path.join(SMARTVESSEL_DIR, "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def read_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/{page_name}.html")
    def read_page(page_name: str):
        page_path = os.path.join(FRONTEND_DIR, f"{page_name}.html")
        if os.path.exists(page_path):
            return FileResponse(page_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

