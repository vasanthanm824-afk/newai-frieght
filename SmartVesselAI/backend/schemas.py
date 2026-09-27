from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Forecast Schemas
class ForecastRequest(BaseModel):
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    vessel_type: str = Field(default="Panamax")
    cargo_tonnes: float = Field(default=80000.0)

class ForecastResponse(BaseModel):
    origin: str
    destination: str
    vessel_type: str
    current_rate: float
    forecast_7d: float
    forecast_14d: float
    forecast_30d: float
    trend: str
    historical_dates: List[str]
    historical_rates: List[float]
    forecast_dates: List[str]
    forecast_rates: List[float]

# Vessel & Port Compatibility Schemas
class CompatibilityRequest(BaseModel):
    vessel_name: str = Field(default="Panamax Explorer")
    cargo_tonnes: float = Field(default=80000.0)
    port_name: str = Field(default="Paradip")

class VesselInfo(BaseModel):
    vessel_id: str
    vessel_name: str
    vessel_type: str
    capacity: float
    loa: float
    beam: float
    draft: float
    speed: float

class PortInfo(BaseModel):
    port_id: str
    port_name: str
    country: str
    max_draft: float
    max_loa: float
    max_beam: float
    handling_capacity: float

class CompatibilityResponse(BaseModel):
    is_compatible: bool
    draft_check: dict
    loa_check: dict
    beam_check: dict
    capacity_check: dict
    reasons: List[str]

# Optimization Schemas
class OptimizationRequest(BaseModel):
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    cargo_tonnes: float = Field(default=80000.0)
    commodity: str = Field(default="Coal")
    required_date: str = Field(default="2026-09-15")

class VesselCostBreakdown(BaseModel):
    vessel_name: str
    vessel_type: str
    is_compatible: bool
    freight_cost: float
    fuel_cost: float
    port_cost: float
    waiting_cost: float
    idle_cost: float
    risk_penalty: float
    total_cost: float
    score: float
    risk_level: str
    recommendation_action: str # BUY, WAIT, CHARTER

class OptimizationResponse(BaseModel):
    cargo_summary: dict
    recommended_vessel: str
    recommended_action: str
    estimated_total_cost: float
    explanation: List[str]
    all_options: List[VesselCostBreakdown]

# Telemetry Schema
class TelemetryCreate(BaseModel):
    vessel_id: str
    latitude: float
    longitude: float
    speed: float
    temperature: float
    humidity: float
    pitch: float
    roll: float
    status: str

class TelemetryResponse(TelemetryCreate):
    id: int
    timestamp: str

# Bill & Process Schemas
class BillRequest(BaseModel):
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    cargo_tonnes: float = Field(default=80000.0)
    commodity: str = Field(default="Coal")
    vessel_type: str = Field(default="Panamax")

class BillResponse(BaseModel):
    bill_id: str
    generated_at: str
    client_summary: dict
    forecast_summary: dict
    recommended_vessel: dict
    port_compliance: dict
    itemized_costs: dict
    total_bill_amount_lakhs: float
    recommendation_action: str
    explanations: List[str]
