"""Doubly Linked List Data Structure & Algorithm for Shipping Voyage Route Navigation."""
from __future__ import annotations

from typing import Any, Optional
import pandas as pd

from freight_pipeline import (
    INDIAN_EAST_COAST_PORTS,
    ORIGIN_PORTS,
    SAILING_DISTANCES_NM,
    VESSEL_CATALOG,
    get_sailing_distance,
)


class VoyageNode:
    """Represents a single node in the voyage doubly linked list."""

    def __init__(
        self,
        node_id: str,
        title: str,
        node_type: str,  # "PORT_ORIGIN", "TRANSIT_LEG", "BUNKER_HUB", "PORT_DESTINATION"
        location_name: str,
        country: str,
        vessel_type: str,
        distance_nm: float = 0.0,
        est_days: float = 0.0,
        cost_usd: float = 0.0,
        risk_level: str = "LOW",
        details: Optional[dict[str, Any]] = None,
    ):
        self.node_id = node_id
        self.title = title
        self.node_type = node_type
        self.location_name = location_name
        self.country = country
        self.vessel_type = vessel_type
        self.distance_nm = distance_nm
        self.est_days = est_days
        self.cost_usd = cost_usd
        self.risk_level = risk_level
        self.details = details or {}

        # Doubly Linked List Pointers
        self.prev_node: Optional[VoyageNode] = None
        self.next_node: Optional[VoyageNode] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize node and its pointer references into dictionary format."""
        return {
            "node_id": self.node_id,
            "title": self.title,
            "node_type": self.node_type,
            "location_name": self.location_name,
            "country": self.country,
            "vessel_type": self.vessel_type,
            "distance_nm": self.distance_nm,
            "est_days": self.est_days,
            "cost_usd": self.cost_usd,
            "risk_level": self.risk_level,
            "details": self.details,
            "prev_id": self.prev_node.node_id if self.prev_node else None,
            "next_id": self.next_node.node_id if self.next_node else None,
        }


class VoyageLinkedList:
    """Doubly Linked List managing a sequence of shipping voyage nodes."""

    def __init__(self):
        self.head: Optional[VoyageNode] = None
        self.tail: Optional[VoyageNode] = None
        self.size: int = 0

    def append(self, node: VoyageNode) -> None:
        """Append node to the end of the doubly linked list."""
        if not self.head:
            self.head = node
            self.tail = node
        else:
            assert self.tail is not None
            self.tail.next_node = node
            node.prev_node = self.tail
            self.tail = node
        self.size += 1

    def insert_after(self, target_node_id: str, new_node: VoyageNode) -> bool:
        """Insert new_node after target_node_id in the linked list."""
        current = self.head
        while current:
            if current.node_id == target_node_id:
                new_node.next_node = current.next_node
                new_node.prev_node = current
                if current.next_node:
                    current.next_node.prev_node = new_node
                else:
                    self.tail = new_node
                current.next_node = new_node
                self.size += 1
                return True
            current = current.next_node
        return False

    def remove_node(self, node_id: str) -> bool:
        """Remove node from the doubly linked list."""
        current = self.head
        while current:
            if current.node_id == node_id:
                if current.prev_node:
                    current.prev_node.next_node = current.next_node
                else:
                    self.head = current.next_node

                if current.next_node:
                    current.next_node.prev_node = current.prev_node
                else:
                    self.tail = current.prev_node

                self.size -= 1
                return True
            current = current.next_node
        return False

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Traverse list from head to tail and return list of node dicts."""
        nodes = []
        current = self.head
        while current:
            nodes.append(current.to_dict())
            current = current.next_node
        return nodes

    def compute_total_metrics(self) -> dict[str, Any]:
        """Traverse linked list and aggregate total distance, days, costs, and risk profile."""
        total_dist = 0.0
        total_days = 0.0
        total_cost = 0.0
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}

        current = self.head
        while current:
            total_dist += current.distance_nm
            total_days += current.est_days
            total_cost += current.cost_usd
            risk_counts[current.risk_level] = risk_counts.get(current.risk_level, 0) + 1
            current = current.next_node

        overall_risk = "HIGH" if risk_counts.get("HIGH", 0) > 0 else ("MEDIUM" if risk_counts.get("MEDIUM", 0) > 0 else "LOW")

        return {
            "total_nodes": self.size,
            "total_distance_nm": round(total_dist, 1),
            "total_voyage_days": round(total_days, 1),
            "total_cost_usd": round(total_cost, 2),
            "overall_risk": overall_risk,
            "risk_counts": risk_counts,
        }


def build_route_linked_list(
    origin_country: str = "Australia",
    origin_port: str = "Newcastle",
    destination_country: str = "India",
    destination_port: str = "Paradip",
    vessel_type: str = "Supramax",
    cargo_tonnes: float = 50000,
) -> tuple[VoyageLinkedList, dict[str, Any]]:
    """Build a 5-node doubly linked list sequence for shipping voyage navigation."""
    v_linked_list = VoyageLinkedList()

    vessel_info = next((v for v in VESSEL_CATALOG if v["vessel_type"] == vessel_type), VESSEL_CATALOG[1])
    speed = vessel_info["speed_knots"]
    dwt = vessel_info["dwt"]
    draft_m = vessel_info["draft_m"]

    dist_total = get_sailing_distance(origin_country, destination_country, destination_port)
    dist_leg1 = round(dist_total * 0.45, 1)
    dist_leg2 = round(dist_total * 0.55, 1)

    sailing_days1 = round(dist_leg1 / (speed * 24.0), 1)
    sailing_days2 = round(dist_leg2 / (speed * 24.0), 1)

    # Node 1: Origin Port Loading
    node1 = VoyageNode(
        node_id="node_1_origin",
        title=f"Loading Port: {origin_port}",
        node_type="PORT_ORIGIN",
        location_name=origin_port,
        country=origin_country,
        vessel_type=vessel_type,
        distance_nm=0.0,
        est_days=2.5,
        cost_usd=45000.0,
        risk_level="LOW",
        details={
            "operation": "Cargo Loading & Port Berth Clearance",
            "handling_tpd": 15000,
            "max_draft_m": 15.5,
            "max_loa_m": 290,
            "cargo_loaded_mt": cargo_tonnes,
        },
    )
    v_linked_list.append(node1)

    # Node 2: Ocean Sailing Leg 1
    node2 = VoyageNode(
        node_id="node_2_transit1",
        title=f"Ocean Passage: {origin_port} → Bunkering Waypoint",
        node_type="TRANSIT_LEG",
        location_name="Indian Ocean Passage (South)",
        country="Open Ocean",
        vessel_type=vessel_type,
        distance_nm=dist_leg1,
        est_days=sailing_days1,
        cost_usd=round(sailing_days1 * 14500.0, 2),
        risk_level="LOW",
        details={
            "sailing_speed_knots": speed,
            "vessel_hire_per_day": 14500.0,
            "weather_condition": "Fair / Calm Sea State",
            "fuel_consumed_vlsfo_mt": round(sailing_days1 * 28.0, 1),
        },
    )
    v_linked_list.append(node2)

    # Node 3: Bunkering & Refueling Hub
    bunker_hub = "Singapore" if origin_country in ("Australia", "Indonesia", "Japan", "China", "Vietnam") else "Fujairah"
    node3 = VoyageNode(
        node_id="node_3_bunker",
        title=f"Bunker Refueling Hub: {bunker_hub}",
        node_type="BUNKER_HUB",
        location_name=bunker_hub,
        country="Singapore" if bunker_hub == "Singapore" else "UAE",
        vessel_type=vessel_type,
        distance_nm=0.0,
        est_days=1.0,
        cost_usd=165000.0,
        risk_level="LOW",
        details={
            "bunker_vlsfo_price_usd_mt": 612.5,
            "bunker_volume_mt": 270.0,
            "bunkering_time_hours": 18,
            "port_dues_usd": 12000.0,
        },
    )
    v_linked_list.append(node3)

    # Node 4: Ocean Sailing Leg 2
    node4 = VoyageNode(
        node_id="node_4_transit2",
        title=f"Ocean Passage: {bunker_hub} → {destination_port}",
        node_type="TRANSIT_LEG",
        location_name="Bay of Bengal Approach",
        country="Open Ocean",
        vessel_type=vessel_type,
        distance_nm=dist_leg2,
        est_days=sailing_days2,
        cost_usd=round(sailing_days2 * 14500.0, 2),
        risk_level="MEDIUM" if destination_port in ("Gopalpur", "Sagar-Sandheads") else "LOW",
        details={
            "sailing_speed_knots": speed,
            "vessel_hire_per_day": 14500.0,
            "sea_swell_m": 2.2,
            "fuel_consumed_vlsfo_mt": round(sailing_days2 * 28.0, 1),
        },
    )
    v_linked_list.append(node4)

    # Node 5: Destination Discharge Port
    node5 = VoyageNode(
        node_id="node_5_destination",
        title=f"Discharge Port: {destination_port}",
        node_type="PORT_DESTINATION",
        location_name=destination_port,
        country=destination_country,
        vessel_type=vessel_type,
        distance_nm=0.0,
        est_days=3.5,
        cost_usd=62000.0,
        risk_level="HIGH" if destination_port in ("Gopalpur", "Sagar-Sandheads") else "LOW",
        details={
            "operation": "Cargo Discharge & Customs Clearance",
            "handling_tpd": 12000,
            "max_draft_m": draft_m,
            "max_dwt_limit": dwt,
            "berthing_status": "Berth Available",
        },
    )
    v_linked_list.append(node5)

    summary_metrics = v_linked_list.compute_total_metrics()
    return v_linked_list, summary_metrics


# Compatibility alias for process pipeline
generate_voyage_route = build_route_linked_list

