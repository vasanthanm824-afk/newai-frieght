"""Voyage Cost Calculator — end-to-end voyage economics computation.

Computes sailing time, fuel cost, port charges, canal fees, and total
delivered cost for any origin-destination-vessel combination.
"""
from __future__ import annotations

from dataclasses import dataclass

from freight_pipeline import (
    INDIAN_EAST_COAST_PORTS,
    ORIGIN_PORTS,
    SAILING_DISTANCES_NM,
    VESSEL_CATALOG,
    get_origin_port_info,
    get_sailing_distance,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BUNKER_FUEL_USD_PER_MT = 600      # IFO 380 approximate
PORT_ENTRY_HOURS = 12             # average pilotage + berthing
PORT_EXIT_HOURS = 8
SUEZ_CANAL_USD_PER_GT = 8.0       # approximate Suez transit rate


@dataclass
class VoyageCostBreakdown:
    """Detailed breakdown of a single voyage cost."""
    origin_country: str
    origin_port: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    distance_nm: int
    vessel_speed_knots: float
    sailing_days: float
    load_days: float
    unload_days: float
    port_wait_days: float
    total_voyage_days: float
    # Costs
    vessel_hire_usd: float
    fuel_cost_usd: float
    port_charges_load_usd: float
    port_charges_discharge_usd: float
    total_cost_usd: float
    cost_per_tonne: float
    # Feasibility
    feasible_at_origin: bool
    feasible_at_destination: bool
    origin_constraint_note: str
    destination_constraint_note: str


def _check_vessel_feasibility(vessel: dict, port_info: dict) -> tuple[bool, str]:
    """Check if a vessel fits within a port's infrastructure limits."""
    issues = []
    if vessel["loa_m"] > port_info.get("max_loa_m", 999):
        issues.append(f"LOA {vessel['loa_m']}m exceeds limit {port_info.get('max_loa_m', 999)}m")
    if vessel["beam_m"] > port_info.get("max_beam_m", 999):
        issues.append(f"Beam {vessel['beam_m']}m exceeds limit {port_info.get('max_beam_m', 999)}m")
    if vessel["draft_m"] > port_info.get("max_draft_m", 999):
        issues.append(f"Draft {vessel['draft_m']}m exceeds limit {port_info.get('max_draft_m', 999)}m")
    feasible = len(issues) == 0
    note = "; ".join(issues) if issues else "All constraints satisfied"
    return feasible, note


def compute_voyage_cost(
    origin_country: str,
    origin_port: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    bunker_price_usd: float = BUNKER_FUEL_USD_PER_MT,
    destination_country: str = "India",
) -> VoyageCostBreakdown | None:
    """Compute the complete cost breakdown for a single voyage."""
    # Look up vessel
    vessel = next((v for v in VESSEL_CATALOG if v["vessel_type"] == vessel_type), None)
    if vessel is None:
        return None

    # Look up port info
    dest_info = INDIAN_EAST_COAST_PORTS.get(destination_port) or ORIGIN_PORTS.get(destination_country, {}).get(destination_port)
    if dest_info is None:
        dest_info = {"max_loa_m": 300, "max_beam_m": 50, "max_draft_m": 18.0, "handling_tpd": 40000}

    origin_info = get_origin_port_info(origin_country, origin_port)

    # Feasibility checks
    origin_feasible, origin_note = (True, "No origin port data") if origin_info is None else _check_vessel_feasibility(vessel, origin_info)
    dest_feasible, dest_note = _check_vessel_feasibility(vessel, dest_info)

    # Distance
    distance_nm = get_sailing_distance(origin_country, destination_country, destination_port)

    # Time components
    sailing_days = round(distance_nm / (vessel["speed_knots"] * 24), 2)
    load_days = round(cargo_tonnes / vessel["load_tpd"], 2) if vessel["load_tpd"] > 0 else 5.0
    unload_days = round(cargo_tonnes / dest_info.get("handling_tpd", 40000), 2)
    port_wait_days = round((PORT_ENTRY_HOURS + PORT_EXIT_HOURS) * 2 / 24, 2)  # both ports
    total_days = sailing_days + load_days + unload_days + port_wait_days

    # Cost components
    vessel_hire = vessel["daily_cost_usd"] * total_days
    fuel_cost = vessel["fuel_mt_per_day"] * sailing_days * bunker_price_usd
    # Port charges (simplified: based on vessel DWT)
    port_charge_per_gt = 0.5  # $/GT approximation
    port_load = vessel["dwt"] * port_charge_per_gt * 0.3
    port_discharge = vessel["dwt"] * port_charge_per_gt * 0.4
    total_cost = vessel_hire + fuel_cost + port_load + port_discharge
    cost_per_tonne = round(total_cost / cargo_tonnes, 2) if cargo_tonnes > 0 else 0

    return VoyageCostBreakdown(
        origin_country=origin_country,
        origin_port=origin_port,
        destination_port=destination_port,
        vessel_type=vessel_type,
        cargo_tonnes=cargo_tonnes,
        distance_nm=distance_nm,
        vessel_speed_knots=vessel["speed_knots"],
        sailing_days=sailing_days,
        load_days=load_days,
        unload_days=unload_days,
        port_wait_days=port_wait_days,
        total_voyage_days=round(total_days, 1),
        vessel_hire_usd=round(vessel_hire, 0),
        fuel_cost_usd=round(fuel_cost, 0),
        port_charges_load_usd=round(port_load, 0),
        port_charges_discharge_usd=round(port_discharge, 0),
        total_cost_usd=round(total_cost, 0),
        cost_per_tonne=cost_per_tonne,
        feasible_at_origin=origin_feasible,
        feasible_at_destination=dest_feasible,
        origin_constraint_note=origin_note,
        destination_constraint_note=dest_note,
    )


def compare_all_vessels(
    origin_country: str,
    origin_port: str,
    destination_port: str,
    cargo_tonnes: float,
    bunker_price_usd: float = BUNKER_FUEL_USD_PER_MT,
) -> list[VoyageCostBreakdown]:
    """Compute voyage cost for every vessel type and return sorted by cost/tonne."""
    results = []
    for vessel in VESSEL_CATALOG:
        breakdown = compute_voyage_cost(
            origin_country, origin_port, destination_port,
            vessel["vessel_type"], cargo_tonnes, bunker_price_usd,
        )
        if breakdown is not None:
            results.append(breakdown)
    # Sort: feasible first, then by cost_per_tonne
    results.sort(key=lambda x: (
        not (x.feasible_at_origin and x.feasible_at_destination),
        x.cost_per_tonne,
    ))
    return results
