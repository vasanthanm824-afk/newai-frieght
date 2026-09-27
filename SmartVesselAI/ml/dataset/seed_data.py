import os
import sys
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Ensure backend can be imported
SMARTVESSEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if SMARTVESSEL_DIR not in sys.path:
    sys.path.insert(0, SMARTVESSEL_DIR)

try:
    from backend.database import SessionLocal, engine, Base
    from backend.models.db_models import FreightRate, Vessel, Port, Cargo, Telemetry
except ModuleNotFoundError:
    from SmartVesselAI.backend.database import SessionLocal, engine, Base
    from SmartVesselAI.backend.models.db_models import FreightRate, Vessel, Port, Cargo, Telemetry

GLOBAL_PORTS = [
    # India
    {"id": "PRT-001", "name": "Paradip", "country": "India", "draft": 14.5, "loa": 230.0, "beam": 35.0, "cap": 35000, "wait": 2.5},
    {"id": "PRT-002", "name": "Vizag", "country": "India", "draft": 16.5, "loa": 280.0, "beam": 42.0, "cap": 45000, "wait": 1.8},
    {"id": "PRT-005", "name": "Kolkata", "country": "India", "draft": 7.5, "loa": 180.0, "beam": 28.0, "cap": 15000, "wait": 4.0},
    {"id": "PRT-007", "name": "JNPT Mumbai", "country": "India", "draft": 15.0, "loa": 300.0, "beam": 45.0, "cap": 50000, "wait": 2.0},
    {"id": "PRT-008", "name": "Chennai", "country": "India", "draft": 14.0, "loa": 240.0, "beam": 36.0, "cap": 30000, "wait": 2.2},
    {"id": "PRT-009", "name": "Kandla", "country": "India", "draft": 13.0, "loa": 225.0, "beam": 32.5, "cap": 38000, "wait": 3.1},
    {"id": "PRT-010", "name": "Dhamra", "country": "India", "draft": 18.0, "loa": 310.0, "beam": 48.0, "cap": 60000, "wait": 1.5},
    
    # Australia
    {"id": "PRT-003", "name": "Newcastle", "country": "Australia", "draft": 15.2, "loa": 290.0, "beam": 47.0, "cap": 60000, "wait": 1.2},
    {"id": "PRT-011", "name": "Port Hedland", "country": "Australia", "draft": 19.5, "loa": 340.0, "beam": 58.0, "cap": 120000, "wait": 1.0},
    {"id": "PRT-012", "name": "Hay Point", "country": "Australia", "draft": 17.5, "loa": 300.0, "beam": 50.0, "cap": 85000, "wait": 1.4},
    {"id": "PRT-013", "name": "Gladstone", "country": "Australia", "draft": 16.0, "loa": 280.0, "beam": 45.0, "cap": 70000, "wait": 1.6},
    {"id": "PRT-014", "name": "Fremantle", "country": "Australia", "draft": 13.5, "loa": 240.0, "beam": 35.0, "cap": 40000, "wait": 1.1},
    
    # China
    {"id": "PRT-004", "name": "Qingdao", "country": "China", "draft": 20.0, "loa": 340.0, "beam": 60.0, "cap": 80000, "wait": 3.0},
    {"id": "PRT-015", "name": "Shanghai", "country": "China", "draft": 16.0, "loa": 320.0, "beam": 50.0, "cap": 100000, "wait": 2.8},
    {"id": "PRT-016", "name": "Ningbo-Zhoushan", "country": "China", "draft": 22.0, "loa": 360.0, "beam": 65.0, "cap": 110000, "wait": 2.5},
    {"id": "PRT-017", "name": "Tianjin", "country": "China", "draft": 15.5, "loa": 300.0, "beam": 45.0, "cap": 65000, "wait": 3.2},
    
    # South Africa
    {"id": "PRT-006", "name": "Durban", "country": "South Africa", "draft": 12.8, "loa": 240.0, "beam": 33.0, "cap": 25000, "wait": 2.0},
    {"id": "PRT-018", "name": "Richards Bay", "country": "South Africa", "draft": 17.5, "loa": 310.0, "beam": 48.0, "cap": 75000, "wait": 1.7},
    {"id": "PRT-019", "name": "Saldanha Bay", "country": "South Africa", "draft": 20.5, "loa": 330.0, "beam": 55.0, "cap": 90000, "wait": 1.3},
    
    # Brazil
    {"id": "PRT-020", "name": "Tubarao", "country": "Brazil", "draft": 23.0, "loa": 360.0, "beam": 65.0, "cap": 130000, "wait": 1.9},
    {"id": "PRT-021", "name": "Santos", "country": "Brazil", "draft": 14.5, "loa": 280.0, "beam": 42.0, "cap": 55000, "wait": 3.5},
    {"id": "PRT-022", "name": "Itaqui", "country": "Brazil", "draft": 18.5, "loa": 320.0, "beam": 52.0, "cap": 80000, "wait": 2.1},
    
    # USA & Canada
    {"id": "PRT-023", "name": "Houston", "country": "USA", "draft": 14.0, "loa": 270.0, "beam": 40.0, "cap": 50000, "wait": 2.4},
    {"id": "PRT-024", "name": "Los Angeles", "country": "USA", "draft": 16.0, "loa": 310.0, "beam": 48.0, "cap": 85000, "wait": 3.8},
    {"id": "PRT-025", "name": "Baltimore", "country": "USA", "draft": 15.0, "loa": 290.0, "beam": 44.0, "cap": 45000, "wait": 1.8},
    {"id": "PRT-026", "name": "Vancouver", "country": "Canada", "draft": 15.5, "loa": 300.0, "beam": 46.0, "cap": 60000, "wait": 2.0},
    
    # Europe
    {"id": "PRT-027", "name": "Rotterdam", "country": "Netherlands", "draft": 24.0, "loa": 400.0, "beam": 65.0, "cap": 150000, "wait": 1.0},
    {"id": "PRT-028", "name": "Hamburg", "country": "Germany", "draft": 15.0, "loa": 330.0, "beam": 48.0, "cap": 75000, "wait": 1.5},
    
    # Middle East
    {"id": "PRT-029", "name": "Jebel Ali", "country": "UAE", "draft": 16.0, "loa": 350.0, "beam": 54.0, "cap": 95000, "wait": 1.2},
    {"id": "PRT-030", "name": "Ras Tanura", "country": "Saudi Arabia", "draft": 22.0, "loa": 370.0, "beam": 68.0, "cap": 140000, "wait": 1.4},
    {"id": "PRT-031", "name": "Salalah", "country": "Oman", "draft": 17.5, "loa": 320.0, "beam": 50.0, "cap": 70000, "wait": 1.1},
    
    # East / SE Asia
    {"id": "PRT-032", "name": "Singapore", "country": "Singapore", "draft": 18.0, "loa": 400.0, "beam": 60.0, "cap": 160000, "wait": 0.8},
    {"id": "PRT-033", "name": "Yokohama", "country": "Japan", "draft": 16.0, "loa": 300.0, "beam": 48.0, "cap": 65000, "wait": 1.3},
    {"id": "PRT-034", "name": "Busan", "country": "South Korea", "draft": 17.0, "loa": 330.0, "beam": 52.0, "cap": 90000, "wait": 1.4},
    {"id": "PRT-035", "name": "Port Klang", "country": "Malaysia", "draft": 15.0, "loa": 310.0, "beam": 46.0, "cap": 55000, "wait": 1.9},
]

def seed_database(days=730):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Reset tables
    db.query(Port).delete()
    db.query(FreightRate).delete()
    db.query(Vessel).delete()
    db.query(Cargo).delete()
    db.query(Telemetry).delete()

    print(f"Generating high-density multi-year dataset ({days} days) across all global countries & ports...")

    # 1. Vessels
    vessels = [
        Vessel(vessel_id="VES-001", vessel_name="Panamax Explorer", vessel_type="Panamax", capacity=82000, loa=225.0, beam=32.2, draft=13.8, speed=13.5, fuel_consumption=28.5, daily_charter_rate=14500),
        Vessel(vessel_id="VES-002", vessel_name="Cape Titan", vessel_type="Capesize", capacity=180000, loa=292.0, beam=45.0, draft=17.5, speed=12.5, fuel_consumption=42.0, daily_charter_rate=22000),
        Vessel(vessel_id="VES-003", vessel_name="Supramax Horizon", vessel_type="Supramax", capacity=58000, loa=190.0, beam=32.2, draft=12.5, speed=14.0, fuel_consumption=22.0, daily_charter_rate=11500),
        Vessel(vessel_id="VES-004", vessel_name="Handy Wave", vessel_type="Handysize", capacity=35000, loa=175.0, beam=27.0, draft=10.2, speed=14.2, fuel_consumption=18.0, daily_charter_rate=9200),
        Vessel(vessel_id="VES-005", vessel_name="Panamax Pioneer", vessel_type="Panamax", capacity=78000, loa=222.0, beam=32.2, draft=13.2, speed=13.8, fuel_consumption=27.0, daily_charter_rate=13800),
    ]
    db.add_all(vessels)

    # 2. Ports
    port_objs = []
    for p in GLOBAL_PORTS:
        port_objs.append(
            Port(
                port_id=p["id"],
                port_name=p["name"],
                country=p["country"],
                max_draft=p["draft"],
                max_loa=p["loa"],
                max_beam=p["beam"],
                handling_capacity=p["cap"],
                avg_waiting_days=p["wait"]
            )
        )
    db.add_all(port_objs)

    # 3. Cargo Requests
    cargo_items = [
        Cargo(cargo_id="CRG-101", commodity="Coal", quantity=80000, origin="Australia", destination="Paradip", required_date="2026-09-15", status="PENDING"),
        Cargo(cargo_id="CRG-102", commodity="Iron Ore", quantity=150000, origin="Australia", destination="Vizag", required_date="2026-09-20", status="PENDING"),
        Cargo(cargo_id="CRG-103", commodity="Grain", quantity=32000, origin="South Africa", destination="Kolkata", required_date="2026-09-10", status="IN_TRANSIT"),
    ]
    db.add_all(cargo_items)

    # 4. Generate 2-Year Comprehensive Freight Rates across All Country Combinations
    start_date = datetime.now() - timedelta(days=days)
    
    # Extensive trade pairs covering all countries
    trade_pairs = [
        ("Australia", "Paradip", 24.5),
        ("Australia", "Vizag", 22.8),
        ("Australia", "Qingdao", 20.4),
        ("Australia", "Shanghai", 19.8),
        ("Australia", "Busan", 18.5),
        ("Australia", "Yokohama", 21.0),
        ("Brazil", "Qingdao", 23.5),
        ("Brazil", "Paradip", 26.2),
        ("Brazil", "Rotterdam", 17.4),
        ("Brazil", "Dhamra", 25.8),
        ("South Africa", "Kolkata", 29.8),
        ("South Africa", "JNPT Mumbai", 24.2),
        ("South Africa", "Qingdao", 21.6),
        ("USA", "Shanghai", 32.0),
        ("USA", "Rotterdam", 18.2),
        ("USA", "Paradip", 35.4),
        ("Canada", "Busan", 19.8),
        ("Indonesia", "JNPT Mumbai", 19.5),
        ("Indonesia", "Chennai", 16.2),
        ("Saudi Arabia", "Rotterdam", 16.8),
        ("Saudi Arabia", "Paradip", 14.5),
        ("UAE", "Kandla", 12.8),
        ("Oman", "JNPT Mumbai", 11.5),
        ("Singapore", "Busan", 14.2),
        ("Germany", "Jebel Ali", 26.5),
        ("Netherlands", "Singapore", 21.4),
        ("Malaysia", "Yokohama", 15.6),
        ("Japan", "Port Klang", 14.8),
    ]

    vessel_types = ["Panamax", "Capesize", "Supramax", "Handysize"]

    freight_records = []
    total_generated = 0

    for day in range(days):
        curr_date = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
        
        # Macro Trends: Seasonal cycle + Annual inflation trend
        seasonal = 3.0 * np.sin(day / 30.0) + 1.5 * np.cos(day / 90.0)
        macro_bunker_base = 600.0 + 80.0 * np.sin(day / 120.0)

        for orig, dest, base_rate in trade_pairs:
            for vtype in vessel_types:
                # Type multiplier
                v_mult = 1.2 if vtype == "Handysize" else (0.85 if vtype == "Capesize" else 1.0)
                
                noise = np.random.normal(0, 0.5)
                rate = round(max(8.0, (base_rate * v_mult) + seasonal + noise), 2)
                fuel = round(max(400.0, macro_bunker_base + noise * 12), 2)
                weather = round(min(1.0, max(0.0, 0.1 + random.random() * 0.25)), 2)
                congestion = round(min(1.0, max(0.0, 0.15 + random.random() * 0.3)), 2)

                freight_records.append(
                    FreightRate(
                        date=curr_date,
                        origin=orig,
                        destination=dest,
                        vessel_type=vtype,
                        freight_rate=rate,
                        fuel_price=fuel,
                        weather_risk=weather,
                        congestion_index=congestion
                    )
                )
                total_generated += 1

                # Batch insert to handle large record count efficiently
                if len(freight_records) >= 5000:
                    db.add_all(freight_records)
                    db.commit()
                    freight_records = []

    if freight_records:
        db.add_all(freight_records)
        db.commit()

    # 5. Telemetry
    telemetry_records = [
        Telemetry(vessel_id="VES-001", latitude=11.62, longitude=92.72, speed=13.4, temperature=28.5, humidity=75.0, pitch=1.2, roll=2.1, status="IN_TRANSIT"),
        Telemetry(vessel_id="VES-002", latitude=-20.15, longitude=118.57, speed=12.1, temperature=26.0, humidity=68.0, pitch=0.8, roll=1.5, status="LOADING"),
        Telemetry(vessel_id="VES-003", latitude=20.26, longitude=86.67, speed=0.5, temperature=31.2, humidity=82.0, pitch=0.2, roll=0.4, status="DISCHARGING"),
    ]
    db.add_all(telemetry_records)

    db.commit()
    print(f"Database successfully seeded with {total_generated:,} freight records spanning {days} days across all countries!")
    db.close()
    return total_generated

if __name__ == "__main__":
    seed_database(730)
