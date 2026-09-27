"""Vessels router — recommendations, catalog, feasibility matrix."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.freight_pipeline import (
    INDIAN_EAST_COAST_PORTS,
    VESSEL_CATALOG,
    recommend_vessels,
)

router = APIRouter()


class VesselRequest(BaseModel):
    origin_country: str
    destination_port: str
    cargo_tonnes: float
    origin_port: str | None = None


@router.post("/recommend")
def get_recommendations(req: VesselRequest):
    rec = recommend_vessels(
        req.origin_country, req.destination_port, req.cargo_tonnes, req.origin_port,
    )
    return {"vessels": rec.to_dict(orient="records")}


@router.get("/catalog")
def get_catalog():
    return {"vessels": VESSEL_CATALOG}


@router.get("/feasibility-matrix")
def feasibility_matrix():
    matrix = []
    for port_name, port_info in INDIAN_EAST_COAST_PORTS.items():
        row = {"port": port_name}
        for vessel in VESSEL_CATALOG:
            feasible = (
                vessel["loa_m"] <= port_info["max_loa_m"]
                and vessel["beam_m"] <= port_info["max_beam_m"]
                and vessel["draft_m"] <= port_info["max_draft_m"]
            )
            row[vessel["vessel_type"]] = feasible
        matrix.append(row)
    return {"matrix": matrix}
