"""Risk router — alerts, route assessment, monsoon calendar."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.freight_pipeline import (
    INDIAN_EAST_COAST_PORTS,
    INDIAN_PORT_LIST,
    evaluate_shipment_date,
    forecast_rates,
    risk_alerts,
)
from ..state import get_feature_columns, get_model

router = APIRouter()


class RiskRequest(BaseModel):
    origin_country: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    months: int = 6


@router.post("/alerts")
def get_alerts(req: RiskRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    fc = forecast_rates(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, months=req.months, feature_columns=get_feature_columns(),
    )
    alerts = risk_alerts(fc, {
        "cargo_tonnes": req.cargo_tonnes,
        "destination_port": req.destination_port,
        "origin_country": req.origin_country,
    })
    return {"alerts": alerts}


@router.post("/route-assessment")
def route_assessment(req: RiskRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    results = []
    for port in INDIAN_PORT_LIST:
        try:
            pf = forecast_rates(
                model, req.origin_country, port, req.vessel_type,
                req.cargo_tonnes, months=6, feature_columns=get_feature_columns(),
            )
            port_alerts = risk_alerts(pf, {
                "cargo_tonnes": req.cargo_tonnes,
                "destination_port": port,
                "origin_country": req.origin_country,
            })
            avg_rate = float(pf["rate_usd_per_ton"].mean())
            volatility = float(pf["rate_std"].mean()) if "rate_std" in pf.columns else 0
            risk_score = len([a for a in port_alerts if "✅" not in a])
            results.append({
                "port": port,
                "avg_rate": round(avg_rate, 2),
                "volatility": round(volatility, 2),
                "alert_count": risk_score,
                "risk_level": "LOW" if risk_score <= 1 else ("MEDIUM" if risk_score <= 2 else "HIGH"),
            })
        except Exception:
            pass
    return {"assessment": results}


@router.get("/monsoon")
def monsoon_calendar():
    data = []
    for port_name, port_info in INDIAN_EAST_COAST_PORTS.items():
        severity = "SEVERE" if port_name in ("Gopalpur", "Sagar-Sandheads") else (
            "MODERATE" if port_name in ("Haldia", "Paradip") else "MILD"
        )
        data.append({
            "port": port_name,
            "state": port_info["state"],
            "severity": severity,
            "action": (
                "Avoid scheduling Jun-Aug" if severity == "SEVERE"
                else ("Plan buffer days" if severity == "MODERATE" else "Normal operations")
            ),
        })
    return {"monsoon": data}


class DateEvaluationRequest(BaseModel):
    target_date: str
    origin_country: str
    origin_port: str | None = None
    destination_country: str = "India"
    destination_port: str = "Paradip"
    vessel_type: str = "Supramax"
    cargo_tonnes: float = 50000


@router.post("/evaluate-date")
def evaluate_date(req: DateEvaluationRequest):
    model = get_model()
    result = evaluate_shipment_date(
        target_date_str=req.target_date,
        origin_country=req.origin_country,
        origin_port=req.origin_port,
        destination_country=req.destination_country,
        destination_port=req.destination_port,
        vessel_type=req.vessel_type,
        cargo_tonnes=req.cargo_tonnes,
        model=model,
        feature_columns=get_feature_columns(),
    )
    return result


@router.post("/live-alerts")
def get_live_risk_matrix(req: RiskRequest):
    """Categorized risk matrix with severity ratings and mitigation strategies."""
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}

    fc = forecast_rates(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, months=req.months, feature_columns=get_feature_columns(),
    )
    raw_alerts = risk_alerts(fc, {
        "cargo_tonnes": req.cargo_tonnes,
        "destination_port": req.destination_port,
        "origin_country": req.origin_country,
    })

    # Weather / Monsoon Risk
    port_info = INDIAN_EAST_COAST_PORTS.get(req.destination_port, {})
    draft_m = port_info.get("draft_m", 14.0)
    
    categorized_matrix = []

    # Category 1: Weather & Monsoon
    if req.destination_port in ["Gopalpur", "Sagar-Sandheads"]:
        categorized_matrix.append({
            "category": "Weather & Monsoon Operational Risk",
            "severity": "HIGH",
            "title": f"Southwest Monsoon Congestion at {req.destination_port}",
            "description": "High swell and severe weather exposure during SW monsoon (Jun-Aug).",
            "mitigation": "Schedule vessel arrivals before mid-May or consider lightering options.",
        })
    else:
        categorized_matrix.append({
            "category": "Weather & Monsoon Operational Risk",
            "severity": "LOW",
            "title": f"Normal Operational Conditions at {req.destination_port}",
            "description": "Port handles seasonal weather variations with standard anchorage protocols.",
            "mitigation": "Maintain standard 24h ETA notification buffer.",
        })

    # Category 2: Rate Volatility
    avg_rate = float(fc["rate_usd_per_ton"].mean())
    max_rate = float(fc["rate_usd_per_ton"].max())
    volatility_pct = ((max_rate - avg_rate) / avg_rate) * 100 if avg_rate > 0 else 0

    if volatility_pct > 15:
        categorized_matrix.append({
            "category": "Freight Rate Volatility Risk",
            "severity": "MEDIUM",
            "title": f"High Rate Variance Detected ({volatility_pct:.1f}% spread)",
            "description": "Forecast indicates significant month-to-month freight rate fluctuations.",
            "mitigation": "Consider hedging via Contract of Affreightment (CoA) or index-linked FFA.",
        })
    else:
        categorized_matrix.append({
            "category": "Freight Rate Volatility Risk",
            "severity": "LOW",
            "title": "Stable Spot Market Outlook",
            "description": "Freight rate projections show steady trajectory over the forecast horizon.",
            "mitigation": "Spot booking is viable with low price volatility risk.",
        })

    # Category 3: Port Draft & Capacity
    vessel_req_draft = 14.0 if req.vessel_type == "Capesize" else (12.5 if req.vessel_type == "Panamax" else 11.0)
    if draft_m < vessel_req_draft:
        categorized_matrix.append({
            "category": "Port Draft & Cargo Capacity Risk",
            "severity": "CRITICAL",
            "title": f"Vessel Draft Restriction at {req.destination_port}",
            "description": f"{req.vessel_type} requires ~{vessel_req_draft}m draft, but maximum available draft is {draft_m}m.",
            "mitigation": f"Switch to smaller vessel class (e.g. Supramax) or plan offshore lightering.",
        })
    else:
        categorized_matrix.append({
            "category": "Port Draft & Cargo Capacity Risk",
            "severity": "LOW",
            "title": "Permissible Draft Cleared",
            "description": f"Port draft ({draft_m}m) safely accommodates {req.vessel_type} fully loaded.",
            "mitigation": "No draft restriction adjustments required.",
        })

    # Category 4: Route Security
    if req.origin_country in ["South Africa", "Mozambique"]:
        categorized_matrix.append({
            "category": "Route & Maritime Transit Risk",
            "severity": "MEDIUM",
            "title": "Indian Ocean Weather & Passage Monitoring",
            "description": "Cape route transit subject to seasonal swell and piracy watch area advisories.",
            "mitigation": "Ensure BMP5 security compliance and monitor weather routing services.",
        })
    else:
        categorized_matrix.append({
            "category": "Route & Maritime Transit Risk",
            "severity": "LOW",
            "title": "Direct Open Ocean Corridor",
            "description": "Standard shipping lane with active naval surveillance and clear navigation.",
            "mitigation": "Standard maritime passage planning.",
        })

    # Calculate overall risk score
    severity_weights = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}
    max_severity = max((c["severity"] for c in categorized_matrix), key=lambda s: severity_weights[s])

    return {
        "status": "success",
        "overall_risk_level": max_severity,
        "raw_alerts": raw_alerts,
        "risk_matrix": categorized_matrix,
    }

