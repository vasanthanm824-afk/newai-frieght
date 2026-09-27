"""Linked List router — doubly linked list route sequence, insertion, and deletion."""
from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..core.linked_list_route import (
    VoyageLinkedList,
    VoyageNode,
    build_route_linked_list,
)

router = APIRouter()


class BuildRouteRequest(BaseModel):
    origin_country: str = "Australia"
    origin_port: str = "Newcastle"
    destination_country: str = "India"
    destination_port: str = "Paradip"
    vessel_type: str = "Supramax"
    cargo_tonnes: float = 50000


class InsertNodeRequest(BaseModel):
    target_node_id: str
    new_node_title: str
    location_name: str
    country: str = "Transit Port"
    vessel_type: str = "Supramax"
    distance_nm: float = 250.0
    est_days: float = 1.0
    cost_usd: float = 25000.0
    risk_level: str = "LOW"
    current_nodes: list[dict[str, Any]]


class RemoveNodeRequest(BaseModel):
    node_id: str
    current_nodes: list[dict[str, Any]]


@router.post("/build-route")
def build_route(req: BuildRouteRequest):
    """Build a doubly linked list sequence for a voyage route."""
    v_list, summary = build_route_linked_list(
        origin_country=req.origin_country,
        origin_port=req.origin_port,
        destination_country=req.destination_country,
        destination_port=req.destination_port,
        vessel_type=req.vessel_type,
        cargo_tonnes=req.cargo_tonnes,
    )
    return {
        "status": "success",
        "nodes": v_list.to_dict_list(),
        "summary": summary,
    }


@router.post("/insert-node")
def insert_node(req: InsertNodeRequest):
    """Insert a custom node after target_node_id in the doubly linked list."""
    v_list = VoyageLinkedList()
    for n in req.current_nodes:
        v_node = VoyageNode(
            node_id=n["node_id"],
            title=n["title"],
            node_type=n["node_type"],
            location_name=n["location_name"],
            country=n["country"],
            vessel_type=n["vessel_type"],
            distance_nm=n.get("distance_nm", 0.0),
            est_days=n.get("est_days", 0.0),
            cost_usd=n.get("cost_usd", 0.0),
            risk_level=n.get("risk_level", "LOW"),
            details=n.get("details", {}),
        )
        v_list.append(v_node)

    new_id = f"node_waypoint_{v_list.size + 1}"
    new_node = VoyageNode(
        node_id=new_id,
        title=req.new_node_title,
        node_type="TRANSIT_LEG",
        location_name=req.location_name,
        country=req.country,
        vessel_type=req.vessel_type,
        distance_nm=req.distance_nm,
        est_days=req.est_days,
        cost_usd=req.cost_usd,
        risk_level=req.risk_level,
        details={"inserted_by_user": True},
    )

    success = v_list.insert_after(req.target_node_id, new_node)
    return {
        "status": "success" if success else "error",
        "nodes": v_list.to_dict_list(),
        "summary": v_list.compute_total_metrics(),
    }


@router.post("/remove-node")
def remove_node(req: RemoveNodeRequest):
    """Remove a node from the doubly linked list."""
    v_list = VoyageLinkedList()
    for n in req.current_nodes:
        v_node = VoyageNode(
            node_id=n["node_id"],
            title=n["title"],
            node_type=n["node_type"],
            location_name=n["location_name"],
            country=n["country"],
            vessel_type=n["vessel_type"],
            distance_nm=n.get("distance_nm", 0.0),
            est_days=n.get("est_days", 0.0),
            cost_usd=n.get("cost_usd", 0.0),
            risk_level=n.get("risk_level", "LOW"),
            details=n.get("details", {}),
        )
        v_list.append(v_node)

    success = v_list.remove_node(req.node_id)
    return {
        "status": "success" if success else "error",
        "nodes": v_list.to_dict_list(),
        "summary": v_list.compute_total_metrics(),
    }
