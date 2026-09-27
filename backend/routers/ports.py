"""Ports router — Indian East Coast & origin port data."""
from __future__ import annotations

from fastapi import APIRouter

from ..core.freight_pipeline import (
    COUNTRY_OPTIONS,
    INDIAN_EAST_COAST_PORTS,
    INDIAN_PORT_LIST,
    ORIGIN_COUNTRY_LIST,
    ORIGIN_PORTS,
    SAILING_DISTANCES_NM,
    VESSEL_CATALOG,
    get_ports_for_country,
)

router = APIRouter()


@router.get("/origin-countries")
def list_origin_countries():
    return {"countries": ORIGIN_COUNTRY_LIST}


@router.get("/all-countries")
def list_all_countries():
    return {"countries": COUNTRY_OPTIONS}


@router.get("/by-country")
def list_ports_by_country(country: str):
    ports = get_ports_for_country(country)
    port_details = ORIGIN_PORTS.get(country, {}) if country != "India" else INDIAN_EAST_COAST_PORTS
    return {"country": country, "ports": port_details, "port_names": ports}


@router.get("/origin")
def list_origin_ports(country: str | None = None):
    if country:
        ports = ORIGIN_PORTS.get(country, {})
        return {"country": country, "ports": ports}
    return {"ports": ORIGIN_PORTS}


@router.get("/indian")
def list_indian_ports():
    return {"ports": INDIAN_EAST_COAST_PORTS, "port_names": INDIAN_PORT_LIST}


@router.get("/distances")
def get_distances():
    return {"distances": SAILING_DISTANCES_NM}


@router.get("/vessels")
def get_vessel_catalog():
    return {"vessels": VESSEL_CATALOG}
