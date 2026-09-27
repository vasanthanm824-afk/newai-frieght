"""Process router — unified end-to-end processing pipeline for user shipment data."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, date
import time
from fastapi import APIRouter
from pydantic import BaseModel, Field

try:
    from ..core.freight_pipeline import (
        INDIAN_EAST_COAST_PORTS,
        INDIAN_PORT_LIST,
        evaluate_shipment_date,
        forecast_rates,
        recommend_vessels,
        risk_alerts,
    )
    from ..core.voyage_calculator import compare_all_vessels, compute_voyage_cost
    from ..core.contract_optimizer import (
        analyze_idle_scenarios,
        analyze_market_entry,
        compare_contract_strategies,
    )
    from ..core.linked_list_route import generate_voyage_route
    from ..state import get_feature_columns, get_metrics, get_model
except (ImportError, ValueError):
    from backend.core.freight_pipeline import (
        INDIAN_EAST_COAST_PORTS,
        INDIAN_PORT_LIST,
        evaluate_shipment_date,
        forecast_rates,
        recommend_vessels,
        risk_alerts,
    )
    from backend.core.voyage_calculator import compare_all_vessels, compute_voyage_cost
    from backend.core.contract_optimizer import (
        analyze_idle_scenarios,
        analyze_market_entry,
        compare_contract_strategies,
    )
    from backend.core.linked_list_route import (
        VoyageLinkedList,
        VoyageNode,
        build_route_linked_list,
    )
    from backend.state import get_feature_columns, get_metrics, get_model



router = APIRouter()


class ProcessShipmentRequest(BaseModel):
    origin_country: str = "Australia"
    destination_country: str = "India"
    origin_port: str = "Newcastle"
    destination_port: str = "Paradip"
    target_shipment_date: str = Field(default_factory=lambda: date.today().isoformat())
    cargo_tonnes: float = 50000.0
    vessel_type: str = "Auto (Optimize)"
    forecast_months: int = 6
    voyages_per_year: int = 6


@router.post("")
def process_shipment_data(req: ProcessShipmentRequest):
    """Execute complete end-to-end processing pipeline on user-submitted shipment data."""
    start_time = time.time()
    
    # 1. Determine optimal vessel if auto
    model = get_model()
    feature_cols = get_feature_columns()
    
    actual_vessel_type = req.vessel_type
    rec_vessel_list = []
    if req.vessel_type == "Auto (Optimize)" or not req.vessel_type:
        try:
            rec_df = recommend_vessels(
                req.origin_country, req.destination_port, req.cargo_tonnes, req.origin_port
            )
            if not rec_df.empty:
                actual_vessel_type = rec_df.iloc[0]["vessel_type"]
                rec_vessel_list = rec_df.to_dict(orient="records")
            else:
                actual_vessel_type = "Supramax"
        except Exception:
            actual_vessel_type = "Supramax"

    # Parse shipment date
    try:
        parsed_date = datetime.strptime(req.target_shipment_date, "%Y-%m-%d").date()
    except Exception:
        parsed_date = date.today()

    # 2. Rate Forecast Calculation
    forecast_records = []
    forecast_summary = {}
    if model is not None:
        try:
            fc_df = forecast_rates(
                model,
                req.origin_country,
                req.destination_port,
                actual_vessel_type,
                req.cargo_tonnes,
                months=req.forecast_months,
                feature_columns=feature_cols,
                origin_port=req.origin_port,
            )
            if not fc_df.empty:
                forecast_records = fc_df.to_dict(orient="records")
                # Format datetime string
                for r in forecast_records:
                    if "shipment_date" in r and hasattr(r["shipment_date"], "isoformat"):
                        r["shipment_date"] = r["shipment_date"].isoformat()
                
                avg_rate = float(fc_df["rate_usd_per_ton"].mean())
                min_rate = float(fc_df["rate_usd_per_ton"].min())
                max_rate = float(fc_df["rate_usd_per_ton"].max())
                latest_rate = float(fc_df["rate_usd_per_ton"].iloc[-1])
                forecast_summary = {
                    "avg_rate": avg_rate,
                    "min_rate": min_rate,
                    "max_rate": max_rate,
                    "latest_rate": latest_rate,
                    "num_months": len(fc_df),
                }
        except Exception as e:
            forecast_summary["error"] = str(e)

    # 3. Voyage Cost Calculation & Vessel Comparison
    voyage_calc_result = None
    all_vessels_comparison = []
    try:
        vc = compute_voyage_cost(
            req.origin_country,
            req.origin_port,
            req.destination_port,
            actual_vessel_type,
            req.cargo_tonnes,
            destination_country=req.destination_country,
        )
        if vc:
            voyage_calc_result = asdict(vc)
        
        cmp_list = compare_all_vessels(
            req.origin_country, req.origin_port, req.destination_port, req.cargo_tonnes
        )
        all_vessels_comparison = [asdict(v) for v in cmp_list]
    except Exception:
        pass

    # 4. Contract Strategy & Market Entry Signal
    contract_strategy = None
    market_entry = None
    idle_scenarios = None
    if model is not None:
        try:
            cs = compare_contract_strategies(
                model,
                req.origin_country,
                req.destination_port,
                actual_vessel_type,
                req.cargo_tonnes,
                req.voyages_per_year,
                feature_cols,
            )
            if cs:
                contract_strategy = asdict(cs)
        except Exception:
            pass

        try:
            me = analyze_market_entry(
                model,
                req.origin_country,
                req.destination_port,
                actual_vessel_type,
                req.cargo_tonnes,
                req.forecast_months,
                feature_cols,
            )
            if me:
                market_entry = asdict(me)
        except Exception:
            pass

        try:
            idl = analyze_idle_scenarios(
                model,
                req.origin_country,
                req.destination_port,
                actual_vessel_type,
                req.cargo_tonnes,
                feature_cols,
            )
            if idl:
                idle_scenarios = [asdict(x) for x in idl]
        except Exception:
            pass

    # 5. Risk Assessment & Weather Feasibility
    feasibility = None
    alerts = []
    try:
        feasibility = evaluate_shipment_date(
            req.destination_port, parsed_date, req.origin_country, actual_vessel_type, req.cargo_tonnes
        )
    except Exception:
        pass

    # 6. Linked List Route Generation
    linked_list_route = None
    try:
        v_list, route_summary = build_route_linked_list(
            origin_country=req.origin_country,
            origin_port=req.origin_port,
            destination_country=req.destination_country,
            destination_port=req.destination_port,
            vessel_type=actual_vessel_type,
            cargo_tonnes=req.cargo_tonnes,
        )
        if v_list:
            linked_list_route = {
                "nodes": v_list.to_dict_list(),
                "summary": route_summary,
            }
    except Exception:
        pass


    elapsed = round(time.time() - start_time, 3)

    return {
        "status": "success",
        "processing_time_seconds": elapsed,
        "timestamp": datetime.now().isoformat(),
        "input_parameters": {
            "origin_country": req.origin_country,
            "destination_country": req.destination_country,
            "origin_port": req.origin_port,
            "destination_port": req.destination_port,
            "target_shipment_date": req.target_shipment_date,
            "cargo_tonnes": req.cargo_tonnes,
            "vessel_type_input": req.vessel_type,
            "selected_vessel_type": actual_vessel_type,
            "forecast_months": req.forecast_months,
            "voyages_per_year": req.voyages_per_year,
        },
        "results": {
            "forecast_summary": forecast_summary,
            "forecast_records": forecast_records,
            "recommended_vessels": rec_vessel_list,
            "voyage_cost": voyage_calc_result,
            "all_vessels_comparison": all_vessels_comparison,
            "contract_strategy": contract_strategy,
            "market_entry": market_entry,
            "idle_scenarios": idle_scenarios,
            "weather_feasibility": feasibility,
            "linked_list_route": linked_list_route,
            "model_metrics": get_metrics(),
        },
    }
