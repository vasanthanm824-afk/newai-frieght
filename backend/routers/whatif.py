"""What-If Simulation router — real-time scenario recalculations & decision sensitivity engine."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class WhatIfRequest(BaseModel):
    origin: str = Field(default="Australia")
    destination: str = Field(default="Paradip")
    vessel_type: str = Field(default="Panamax")
    cargo_tonnes: float = Field(default=80000.0)
    spot_rate_usd_t: float = Field(default=25.50)
    fuel_price_usd_mt: float = Field(default=620.0)
    congestion_level: str = Field(default="Medium") # Low, Medium, High
    delay_days_override: float = Field(default=2.5)

@router.post("/what-if")
def simulate_whatif(req: WhatIfRequest):
    usd_to_inr = 83.0
    cargo = req.cargo_tonnes
    
    # Congestion multiplier
    cong_mult = 1.0
    if req.congestion_level.lower() == "high":
        cong_mult = 1.6
    elif req.congestion_level.lower() == "low":
        cong_mult = 0.7
        
    waiting_days = req.delay_days_override * cong_mult
    charter_rate = 14500.0 if req.vessel_type.lower() == "panamax" else (22000.0 if req.vessel_type.lower() == "capesize" else 12500.0)
    
    # 1. Costs calculation in USD
    freight_usd = cargo * req.spot_rate_usd_t
    sailing_days = 12.0
    fuel_usd = sailing_days * 28.0 * req.fuel_price_usd_mt
    port_usd = 18000.0 + (cargo * 0.12)
    waiting_usd = waiting_days * charter_rate
    idle_usd = 1.0 * charter_rate
    risk_delay_usd = 25000.0 * (1.5 if req.congestion_level.lower() == "high" else 1.0)
    
    total_usd = freight_usd + fuel_usd + port_usd + waiting_usd + idle_usd + risk_delay_usd
    total_lakhs = (total_usd * usd_to_inr) / 100000.0
    
    # Base baseline scenario for comparison (Low congestion baseline)
    base_waiting_days = 1.5
    base_waiting_usd = base_waiting_days * charter_rate
    base_total_usd = freight_usd + fuel_usd + port_usd + base_waiting_usd + idle_usd
    base_lakhs = (base_total_usd * usd_to_inr) / 100000.0
    
    cost_delta_lakhs = round(total_lakhs - base_lakhs, 2)
    
    # Decision Engine Logic
    if req.congestion_level.lower() == "high" or waiting_days > 4.0:
        new_decision = "WAIT"
        decision_badge = "🟡 WAIT FOR CLEARANCE"
        action_rationale = f"High congestion ({waiting_days:.1f} days wait) creates ₹{cost_delta_lakhs} L penalty. Postpone chartering by 3-5 days."
    elif req.spot_rate_usd_t < 23.0:
        new_decision = "CHART NOW"
        decision_badge = "🟢 CHART NOW"
        action_rationale = f"Spot freight rate ($ {req.spot_rate_usd_t}/T) is below benchmark average. Lock in vessel immediately."
    else:
        new_decision = "CHART NOW" if waiting_days <= 2.5 else "WAIT"
        decision_badge = "🟢 CHART NOW" if new_decision == "CHART NOW" else "🟡 WAIT"
        action_rationale = "Favorable port turnaround and acceptable daily hire rates."
        
    return {
        "status": "success",
        "parameters": {
            "origin": req.origin,
            "destination": req.destination,
            "vessel_type": req.vessel_type,
            "cargo_tonnes": cargo,
            "spot_rate_usd_t": req.spot_rate_usd_t,
            "fuel_price_usd_mt": req.fuel_price_usd_mt,
            "congestion_level": req.congestion_level,
            "calculated_waiting_days": round(waiting_days, 1)
        },
        "itemized_landed_cost_lakhs": {
            "freight_cost": round((freight_usd * usd_to_inr) / 100000.0, 2),
            "fuel_cost": round((fuel_usd * usd_to_inr) / 100000.0, 2),
            "port_charges": round((port_usd * usd_to_inr) / 100000.0, 2),
            "waiting_cost": round((waiting_usd * usd_to_inr) / 100000.0, 2),
            "risk_delay_cost": round((risk_delay_usd * usd_to_inr) / 100000.0, 2),
            "total_landed_cost": round(total_lakhs, 2)
        },
        "baseline_landed_cost_lakhs": round(base_lakhs, 2),
        "cost_delta_lakhs": cost_delta_lakhs,
        "base_decision": "CHART NOW" if base_lakhs < total_lakhs else "WAIT",
        "new_decision": new_decision,
        "decision_badge": decision_badge,
        "action_rationale": action_rationale,
        "ai_confidence_pct": 86 if req.congestion_level.lower() == "medium" else 92
    }
