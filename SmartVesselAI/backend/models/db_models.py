from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
try:
    from backend.database import Base
except ModuleNotFoundError:
    from ..database import Base

class FreightRate(Base):
    __tablename__ = "freight_rates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    vessel_type = Column(String, index=True)
    freight_rate = Column(Float) # $/tonne or ₹/tonne
    fuel_price = Column(Float, default=620.0) # VLSFO $/MT
    weather_risk = Column(Float, default=0.1) # 0 to 1
    congestion_index = Column(Float, default=0.2) # 0 to 1

class Vessel(Base):
    __tablename__ = "vessels"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(String, unique=True, index=True)
    vessel_name = Column(String)
    vessel_type = Column(String) # Handysize, Supramax, Panamax, Capesize
    capacity = Column(Float) # DWT in tonnes
    loa = Column(Float) # Length overall in meters
    beam = Column(Float) # Beam in meters
    draft = Column(Float) # Max draft in meters
    speed = Column(Float) # Knots
    fuel_consumption = Column(Float) # Tonnes/day
    daily_charter_rate = Column(Float) # $/day

class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(String, unique=True, index=True)
    port_name = Column(String)
    country = Column(String)
    max_draft = Column(Float) # meters
    max_loa = Column(Float) # meters
    max_beam = Column(Float) # meters
    handling_capacity = Column(Float) # Tonnes/day
    avg_waiting_days = Column(Float) # Days

class Cargo(Base):
    __tablename__ = "cargo"

    id = Column(Integer, primary_key=True, index=True)
    cargo_id = Column(String, unique=True, index=True)
    commodity = Column(String) # Coal, Iron Ore, Grain, Bauxite
    quantity = Column(Float) # Tonnes
    origin = Column(String)
    destination = Column(String)
    required_date = Column(String) # YYYY-MM-DD
    status = Column(String, default="PENDING")

class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    pitch = Column(Float)
    roll = Column(Float)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
