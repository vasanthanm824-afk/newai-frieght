"""Reports router — exportable shipment reports in CSV and JSON formats."""
from __future__ import annotations

import csv
import io
from typing import Any, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from .process import ProcessShipmentRequest, process_shipment_data

router = APIRouter()


class ExportReportRequest(ProcessShipmentRequest):
    format: str = Field(default="json", description="Export format: 'json' or 'csv'")


@router.post("/export")
def export_shipment_report(req: ExportReportRequest):
    """Generate and export complete shipment decision report as JSON or CSV."""
    pipeline_result = process_shipment_data(req)
    results = pipeline_result.get("results", {})
    inputs = pipeline_result.get("input_parameters", {})

    if req.format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["=== SHIPMENT ANALYTICS SUMMARY REPORT ==="])
        writer.writerow(["Generated At", pipeline_result.get("timestamp", "")])
        writer.writerow([])
        
        writer.writerow(["--- PARAMETERS ---"])
        for k, v in inputs.items():
            writer.writerow([k, v])
        writer.writerow([])

        # Summary KPIs
        fc_sum = results.get("forecast_summary", {})
        vc = results.get("voyage_cost", {}) or {}
        cs = results.get("contract_strategy", {}) or {}
        me = results.get("market_entry", {}) or {}
        
        writer.writerow(["--- KEY METRICS & STRATEGY ---"])
        writer.writerow(["Average Forecast Rate ($/ton)", fc_sum.get("avg_rate", "N/A")])
        writer.writerow(["Latest Forecast Rate ($/ton)", fc_sum.get("latest_rate", "N/A")])
        writer.writerow(["Voyage Total Cost ($)", vc.get("total_cost_usd", "N/A")])
        writer.writerow(["Voyage Cost per Ton ($)", vc.get("cost_per_tonne", "N/A")])
        writer.writerow(["Recommended Contract Strategy", cs.get("recommended_strategy", "N/A")])
        writer.writerow(["Savings vs Spot ($)", cs.get("savings_vs_spot", "N/A")])
        writer.writerow(["Market Entry Signal", me.get("action", "N/A")])
        writer.writerow(["Signal Confidence", me.get("confidence", "N/A")])
        writer.writerow([])

        # Forecast monthly breakdown
        fc_records = results.get("forecast_records", [])
        if fc_records:
            writer.writerow(["--- MONTHLY FORECAST BREAKDOWN ---"])
            writer.writerow(["Month", "Shipment Date", "Rate ($/ton)", "Lower Bound ($)", "Upper Bound ($)"])
            for r in fc_records:
                writer.writerow([
                    r.get("month", ""),
                    r.get("shipment_date", ""),
                    r.get("rate_usd_per_ton", ""),
                    r.get("rate_lower", ""),
                    r.get("rate_upper", ""),
                ])
            writer.writerow([])

        # Recommended vessels
        rec_vessels = results.get("recommended_vessels", [])
        if rec_vessels:
            writer.writerow(["--- FEASIBLE VESSEL SELECTION ---"])
            writer.writerow(["Vessel Type", "Max Capacity (DWT)", "Suitability Score", "Port Compatibility"])
            for v in rec_vessels:
                writer.writerow([
                    v.get("vessel_type", ""),
                    v.get("max_capacity_dwt", ""),
                    v.get("suitability_score", ""),
                    v.get("port_compatibility", ""),
                ])
            writer.writerow([])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=shipment_report_{inputs.get('destination_port', 'freight')}.csv"},
        )

    # Default JSON Export
    return {
        "status": "success",
        "report_title": f"Shipment Decision Report: {inputs.get('origin_port')} -> {inputs.get('destination_port')}",
        "export_timestamp": pipeline_result.get("timestamp"),
        "summary": {
            "origin": f"{inputs.get('origin_port')}, {inputs.get('origin_country')}",
            "destination": f"{inputs.get('destination_port')}, {inputs.get('destination_country')}",
            "vessel_selected": inputs.get("selected_vessel_type"),
            "cargo_tonnes": inputs.get("cargo_tonnes"),
            "avg_forecast_rate": results.get("forecast_summary", {}).get("avg_rate"),
            "total_voyage_cost_usd": (results.get("voyage_cost") or {}).get("total_cost_usd"),
            "recommended_contract": (results.get("contract_strategy") or {}).get("recommended_strategy"),
            "savings_vs_spot_usd": (results.get("contract_strategy") or {}).get("savings_vs_spot"),
            "market_entry_action": (results.get("market_entry") or {}).get("action"),
        },
        "full_pipeline_data": pipeline_result,
    }
