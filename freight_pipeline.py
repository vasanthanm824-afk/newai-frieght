from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
except ImportError:
    RandomForestRegressor = None
    mean_absolute_error = None
    mean_squared_error = None
    r2_score = None
    train_test_split = None

try:
    from SmartVesselAI.ml.tft_model import TemporalFusionTransformerRegressor
    from SmartVesselAI.ml.gnn_model import GraphNeuralNetworkRegressor
except ModuleNotFoundError:
    from ml.tft_model import TemporalFusionTransformerRegressor
    from ml.gnn_model import GraphNeuralNetworkRegressor

# ---------------------------------------------------------------------------
# Origin countries
# ---------------------------------------------------------------------------
COUNTRY_OPTIONS = [
    "Australia", "Brazil", "China", "India", "Indonesia", "Japan", "Malaysia",
    "Mozambique", "Qatar", "Russia", "Saudi Arabia", "South Africa", "South Korea",
    "Thailand", "UAE", "US", "Vietnam",
]

# ---------------------------------------------------------------------------
# Vessel catalog — key bulk-carrier classes
# ---------------------------------------------------------------------------
VESSEL_CATALOG = [
    {"vessel_type": "Handysize",  "dwt": 30000,  "loa_m": 190, "beam_m": 32, "draft_m": 10.5, "load_tpd": 12000, "daily_cost_usd": 10500, "speed_knots": 13.5, "fuel_mt_per_day": 28},
    {"vessel_type": "Supramax",   "dwt": 55000,  "loa_m": 200, "beam_m": 32, "draft_m": 12.5, "load_tpd": 18000, "daily_cost_usd": 14500, "speed_knots": 14.0, "fuel_mt_per_day": 35},
    {"vessel_type": "Panamax",    "dwt": 75000,  "loa_m": 225, "beam_m": 32, "draft_m": 14.5, "load_tpd": 22000, "daily_cost_usd": 18500, "speed_knots": 14.0, "fuel_mt_per_day": 38},
    {"vessel_type": "Capesize",   "dwt": 160000, "loa_m": 290, "beam_m": 45, "draft_m": 18.0, "load_tpd": 30000, "daily_cost_usd": 26000, "speed_knots": 14.5, "fuel_mt_per_day": 55},
]

VESSEL_TYPE_LIST = [v["vessel_type"] for v in VESSEL_CATALOG]

# ---------------------------------------------------------------------------
# Indian East Coast discharge ports — port-specific infrastructure
# ---------------------------------------------------------------------------
INDIAN_EAST_COAST_PORTS = {
    "Paradip": {
        "state": "Odisha", "max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 17.5,
        "handling_tpd": 47000, "annual_capacity_mt": 120, "berths": 12,
        "notes": "Deep-water, coal-specialized, largest coal import terminal on East Coast",
    },
    "Vizag": {
        "state": "Andhra Pradesh", "max_loa_m": 270, "max_beam_m": 42, "max_draft_m": 16.5,
        "handling_tpd": 42000, "annual_capacity_mt": 75, "berths": 24,
        "notes": "Inner & outer harbor; outer harbor accepts Capesize partially loaded",
    },
    "Gangavaram": {
        "state": "Andhra Pradesh", "max_loa_m": 300, "max_beam_m": 50, "max_draft_m": 18.5,
        "handling_tpd": 55000, "annual_capacity_mt": 64, "berths": 7,
        "notes": "Modern deep-draft port; fully Capesize capable; rapid turnaround",
    },
    "Gopalpur": {
        "state": "Odisha", "max_loa_m": 230, "max_beam_m": 38, "max_draft_m": 14.0,
        "handling_tpd": 25000, "annual_capacity_mt": 20, "berths": 3,
        "notes": "Smaller port; weather-dependent; Panamax limit; seasonal monsoon closures",
    },
    "Dhamra": {
        "state": "Odisha", "max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 18.0,
        "handling_tpd": 50000, "annual_capacity_mt": 100, "berths": 4,
        "notes": "Adani-operated; deep-draft; Capesize capable; efficient mechanized handling",
    },
    "Sagar-Sandheads": {
        "state": "West Bengal", "max_loa_m": 220, "max_beam_m": 36, "max_draft_m": 12.5,
        "handling_tpd": 20000, "annual_capacity_mt": 15, "berths": 2,
        "notes": "Tidal approach; severe draft restriction; lightering operations common",
    },
    "Haldia": {
        "state": "West Bengal", "max_loa_m": 240, "max_beam_m": 38, "max_draft_m": 13.0,
        "handling_tpd": 30000, "annual_capacity_mt": 42, "berths": 13,
        "notes": "River port; tidal constraints; Hooghly river draft limits; monsoon siltation",
    },
}

# ---------------------------------------------------------------------------
# Origin loading ports — port-specific infrastructure per country
# ---------------------------------------------------------------------------
ORIGIN_PORTS = {
    "Australia": {
        "Newcastle":   {"max_loa_m": 300, "max_beam_m": 50, "max_draft_m": 18.3, "handling_tpd": 70000, "commodity": "Thermal Coal"},
        "Hay Point":   {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 18.5, "handling_tpd": 80000, "commodity": "Coking Coal"},
        "Gladstone":   {"max_loa_m": 290, "max_beam_m": 48, "max_draft_m": 17.0, "handling_tpd": 60000, "commodity": "Thermal Coal"},
        "Port Kembla": {"max_loa_m": 270, "max_beam_m": 42, "max_draft_m": 16.0, "handling_tpd": 50000, "commodity": "Coking Coal"},
        "Port Hedland":{"max_loa_m": 340, "max_beam_m": 60, "max_draft_m": 19.5, "handling_tpd": 95000, "commodity": "Iron Ore"},
        "Dampier":     {"max_loa_m": 320, "max_beam_m": 55, "max_draft_m": 19.0, "handling_tpd": 85000, "commodity": "Iron Ore"},
    },
    "Brazil": {
        "Tubarao":     {"max_loa_m": 340, "max_beam_m": 60, "max_draft_m": 22.5, "handling_tpd": 90000, "commodity": "Iron Ore"},
        "Ponta da Madeira": {"max_loa_m": 360, "max_beam_m": 65, "max_draft_m": 23.0, "handling_tpd": 100000, "commodity": "Iron Ore"},
        "Santos":      {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 14.5, "handling_tpd": 45000, "commodity": "Agri/Bulk"},
        "Itaguai":     {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 18.0, "handling_tpd": 65000, "commodity": "Iron Ore/Coal"},
        "Paranagua":   {"max_loa_m": 280, "max_beam_m": 42, "max_draft_m": 13.5, "handling_tpd": 40000, "commodity": "Agri/Bulk"},
    },
    "China": {
        "Qingdao":     {"max_loa_m": 340, "max_beam_m": 60, "max_draft_m": 22.0, "handling_tpd": 85000, "commodity": "Dry Bulk"},
        "Ningbo-Zhoushan": {"max_loa_m": 350, "max_beam_m": 60, "max_draft_m": 22.5, "handling_tpd": 90000, "commodity": "Iron Ore/Coal"},
        "Tianjin":     {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.5, "handling_tpd": 60000, "commodity": "Dry Bulk"},
        "Guangzhou":   {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 14.5, "handling_tpd": 45000, "commodity": "Thermal Coal"},
        "Rizhao":      {"max_loa_m": 320, "max_beam_m": 52, "max_draft_m": 19.0, "handling_tpd": 75000, "commodity": "Iron Ore/Coal"},
    },
    "India": {
        "Paradip":     {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 17.5, "handling_tpd": 47000, "commodity": "Coal/Iron Ore"},
        "Vizag":       {"max_loa_m": 270, "max_beam_m": 42, "max_draft_m": 16.5, "handling_tpd": 42000, "commodity": "Coal/Iron Ore"},
        "Gangavaram":  {"max_loa_m": 300, "max_beam_m": 50, "max_draft_m": 18.5, "handling_tpd": 55000, "commodity": "Coal/Coking"},
        "Gopalpur":    {"max_loa_m": 230, "max_beam_m": 38, "max_draft_m": 14.0, "handling_tpd": 25000, "commodity": "Thermal Coal"},
        "Dhamra":      {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 18.0, "handling_tpd": 50000, "commodity": "Coal"},
        "Sagar-Sandheads": {"max_loa_m": 220, "max_beam_m": 36, "max_draft_m": 12.5, "handling_tpd": 20000, "commodity": "Coal"},
        "Haldia":      {"max_loa_m": 240, "max_beam_m": 38, "max_draft_m": 13.0, "handling_tpd": 30000, "commodity": "Coal/Bulk"},
        "Chennai":     {"max_loa_m": 270, "max_beam_m": 40, "max_draft_m": 15.0, "handling_tpd": 35000, "commodity": "General Bulk"},
        "Tuticorin":   {"max_loa_m": 240, "max_beam_m": 38, "max_draft_m": 14.0, "handling_tpd": 30000, "commodity": "Thermal Coal"},
        "Kakinada":    {"max_loa_m": 250, "max_beam_m": 38, "max_draft_m": 13.5, "handling_tpd": 28000, "commodity": "Bulk"},
        "Kandla":      {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 14.0, "handling_tpd": 38000, "commodity": "Fertilizers/Bulk"},
        "Mundra":      {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 17.5, "handling_tpd": 55000, "commodity": "Thermal Coal"},
        "Mormugao":    {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 14.5, "handling_tpd": 40000, "commodity": "Iron Ore"},
    },
    "Indonesia": {
        "Banjarmasin":  {"max_loa_m": 240, "max_beam_m": 38, "max_draft_m": 13.0, "handling_tpd": 30000, "commodity": "Thermal Coal"},
        "Samarinda":    {"max_loa_m": 230, "max_beam_m": 36, "max_draft_m": 12.5, "handling_tpd": 28000, "commodity": "Thermal Coal"},
        "Balikpapan":   {"max_loa_m": 260, "max_beam_m": 42, "max_draft_m": 14.5, "handling_tpd": 38000, "commodity": "Thermal Coal"},
        "Taboneo":      {"max_loa_m": 290, "max_beam_m": 46, "max_draft_m": 17.0, "handling_tpd": 50000, "commodity": "Thermal Coal"},
        "Tarakan":      {"max_loa_m": 220, "max_beam_m": 34, "max_draft_m": 12.0, "handling_tpd": 22000, "commodity": "Thermal Coal"},
    },
    "Japan": {
        "Yokohama":     {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.0, "handling_tpd": 45000, "commodity": "Dry Bulk"},
        "Kobe":         {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 15.0, "handling_tpd": 40000, "commodity": "Dry Bulk"},
        "Nagoya":       {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.0, "handling_tpd": 50000, "commodity": "Coal/Iron Ore"},
        "Chiba":        {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 17.0, "handling_tpd": 55000, "commodity": "Coal/Raw Materials"},
        "Kitakyushu":   {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 15.0, "handling_tpd": 42000, "commodity": "Iron Ore/Coking"},
    },
    "Malaysia": {
        "Port Klang":   {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.5, "handling_tpd": 45000, "commodity": "General/Bulk"},
        "Johor (Pasir Gudang)": {"max_loa_m": 270, "max_beam_m": 42, "max_draft_m": 14.0, "handling_tpd": 35000, "commodity": "Thermal Coal"},
        "Kuantan":      {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 13.5, "handling_tpd": 30000, "commodity": "Bauxite/Bulk"},
        "Bintulu":      {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 15.0, "handling_tpd": 40000, "commodity": "Coal/LNG"},
    },
    "Mozambique": {
        "Nacala":       {"max_loa_m": 275, "max_beam_m": 43, "max_draft_m": 17.2, "handling_tpd": 43000, "commodity": "Coking Coal"},
        "Beira":        {"max_loa_m": 230, "max_beam_m": 36, "max_draft_m": 12.0, "handling_tpd": 25000, "commodity": "Thermal Coal"},
        "Maputo":       {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 14.5, "handling_tpd": 35000, "commodity": "Thermal Coal"},
    },
    "Qatar": {
        "Ras Laffan":   {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 15.5, "handling_tpd": 60000, "commodity": "LNG/Sulphur"},
        "Hamad Port":   {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 17.0, "handling_tpd": 50000, "commodity": "General Bulk"},
        "Mesaieed":     {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 13.5, "handling_tpd": 35000, "commodity": "Fertilizers/Metals"},
    },
    "Russia": {
        "Vostochny":    {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 18.0, "handling_tpd": 55000, "commodity": "Coking Coal"},
        "Vanino":       {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 15.5, "handling_tpd": 35000, "commodity": "Thermal Coal"},
        "Murmansk":     {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 16.5, "handling_tpd": 48000, "commodity": "Coal/Apatite"},
        "Ust-Luga":     {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 17.5, "handling_tpd": 60000, "commodity": "Coal/Fertilizers"},
        "Novorossiysk": {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 15.0, "handling_tpd": 42000, "commodity": "Grain/Bulk"},
    },
    "Saudi Arabia": {
        "Ras Tanura":   {"max_loa_m": 330, "max_beam_m": 55, "max_draft_m": 20.0, "handling_tpd": 80000, "commodity": "Oil/Bulk"},
        "Jubail":       {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.0, "handling_tpd": 50000, "commodity": "Petrochem/Metals"},
        "Jeddah":       {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 15.5, "handling_tpd": 45000, "commodity": "General Bulk"},
        "Yanbu":        {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.5, "handling_tpd": 48000, "commodity": "Bulk/Minerals"},
    },
    "South Africa": {
        "Richards Bay": {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 18.5, "handling_tpd": 72000, "commodity": "Thermal Coal"},
        "Durban":       {"max_loa_m": 275, "max_beam_m": 42, "max_draft_m": 14.0, "handling_tpd": 38000, "commodity": "Agri/Bulk"},
        "Saldanha Bay": {"max_loa_m": 330, "max_beam_m": 58, "max_draft_m": 20.5, "handling_tpd": 85000, "commodity": "Iron Ore"},
    },
    "South Korea": {
        "Busan":        {"max_loa_m": 320, "max_beam_m": 50, "max_draft_m": 17.0, "handling_tpd": 60000, "commodity": "General Bulk"},
        "Gwangyang":   {"max_loa_m": 330, "max_beam_m": 55, "max_draft_m": 20.0, "handling_tpd": 80000, "commodity": "Iron Ore/Coking"},
        "Pohang":       {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 17.5, "handling_tpd": 65000, "commodity": "Iron Ore/Coal"},
        "Incheon":      {"max_loa_m": 270, "max_beam_m": 40, "max_draft_m": 13.5, "handling_tpd": 35000, "commodity": "Grain/Bulk"},
    },
    "Thailand": {
        "Laem Chabang": {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.0, "handling_tpd": 50000, "commodity": "Bulk/Containers"},
        "Bangkok":      {"max_loa_m": 210, "max_beam_m": 32, "max_draft_m": 11.0, "handling_tpd": 20000, "commodity": "River Bulk"},
        "Map Ta Phut":  {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 14.5, "handling_tpd": 40000, "commodity": "Coal/Industrial"},
    },
    "UAE": {
        "Fujairah":     {"max_loa_m": 330, "max_beam_m": 55, "max_draft_m": 19.0, "handling_tpd": 75000, "commodity": "Bunkers/Bulk"},
        "Jebel Ali":    {"max_loa_m": 340, "max_beam_m": 55, "max_draft_m": 17.0, "handling_tpd": 65000, "commodity": "General Cargo/Bulk"},
        "Ruwais":       {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 15.5, "handling_tpd": 50000, "commodity": "Sulfur/Fertilizers"},
        "Mina Saqr":    {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 14.5, "handling_tpd": 45000, "commodity": "Aggregates/Limestone"},
    },
    "US": {
        "Hampton Roads": {"max_loa_m": 320, "max_beam_m": 52, "max_draft_m": 19.0, "handling_tpd": 65000, "commodity": "Thermal Coal"},
        "Baltimore":     {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 15.5, "handling_tpd": 45000, "commodity": "Thermal Coal"},
        "Mobile":        {"max_loa_m": 275, "max_beam_m": 43, "max_draft_m": 14.5, "handling_tpd": 40000, "commodity": "Thermal Coal"},
        "Houston":       {"max_loa_m": 290, "max_beam_m": 45, "max_draft_m": 14.0, "handling_tpd": 42000, "commodity": "Petcoke/Grain"},
        "New Orleans":   {"max_loa_m": 295, "max_beam_m": 46, "max_draft_m": 14.5, "handling_tpd": 48000, "commodity": "Grain/Coal"},
        "Los Angeles":   {"max_loa_m": 310, "max_beam_m": 50, "max_draft_m": 16.5, "handling_tpd": 55000, "commodity": "Bulk/General"},
    },
    "Vietnam": {
        "Cam Pha":      {"max_loa_m": 260, "max_beam_m": 40, "max_draft_m": 13.5, "handling_tpd": 32000, "commodity": "Thermal Coal"},
        "Hai Phong":    {"max_loa_m": 240, "max_beam_m": 38, "max_draft_m": 12.5, "handling_tpd": 28000, "commodity": "General Bulk"},
        "Phu My":       {"max_loa_m": 280, "max_beam_m": 44, "max_draft_m": 14.5, "handling_tpd": 40000, "commodity": "Grain/Coal"},
        "Vung Tau":     {"max_loa_m": 300, "max_beam_m": 48, "max_draft_m": 16.0, "handling_tpd": 50000, "commodity": "Deepwater Bulk"},
    },
}

# Flat list helpers
ORIGIN_COUNTRY_LIST = list(ORIGIN_PORTS.keys())
INDIAN_PORT_LIST = list(INDIAN_EAST_COAST_PORTS.keys())


def get_ports_for_country(country: str) -> list[str]:
    """Return port names for any country."""
    if country in ORIGIN_PORTS:
        return list(ORIGIN_PORTS[country].keys())
    if country == "India":
        return INDIAN_PORT_LIST
    return []


def get_origin_ports(country: str) -> list[str]:
    """Return the loading port names for a given origin country."""
    return get_ports_for_country(country)


def get_origin_port_info(country: str, port: str) -> dict | None:
    """Return infrastructure dict for a specific origin port."""
    if country in ORIGIN_PORTS and port in ORIGIN_PORTS[country]:
        return ORIGIN_PORTS[country][port]
    if country == "India" and port in INDIAN_EAST_COAST_PORTS:
        return INDIAN_EAST_COAST_PORTS[port]
    return None


def get_indian_port_info(port: str) -> dict | None:
    """Return infrastructure dict for an Indian East Coast discharge port."""
    return INDIAN_EAST_COAST_PORTS.get(port)


# ---------------------------------------------------------------------------
# Sailing distances — nautical miles (NM) between countries / ports
# ---------------------------------------------------------------------------
COUNTRY_DISTANCE_MATRIX: dict[str, dict[str, int]] = {
    "Australia": {"India": 5700, "China": 4200, "Japan": 4300, "South Korea": 4100, "US": 7500, "Brazil": 11500, "South Africa": 5900, "UAE": 6200, "Qatar": 6300, "Saudi Arabia": 6400, "Indonesia": 2200, "Malaysia": 2800, "Thailand": 3100, "Vietnam": 3300, "Mozambique": 5200, "Russia": 5300},
    "Brazil": {"India": 8500, "China": 11000, "Japan": 11500, "South Korea": 11200, "US": 4500, "Australia": 11500, "South Africa": 3300, "UAE": 7200, "Qatar": 7300, "Saudi Arabia": 7400, "Indonesia": 9500, "Malaysia": 9200, "Thailand": 9400, "Vietnam": 9800, "Mozambique": 4800, "Russia": 9800},
    "China": {"India": 3800, "Australia": 4200, "Japan": 1100, "South Korea": 800, "US": 5800, "Brazil": 11000, "South Africa": 6800, "UAE": 5100, "Qatar": 5200, "Saudi Arabia": 5300, "Indonesia": 2100, "Malaysia": 1900, "Thailand": 1600, "Vietnam": 1200, "Mozambique": 6100, "Russia": 1500},
    "India": {"Australia": 5700, "Brazil": 8500, "China": 3800, "Indonesia": 3200, "Japan": 4500, "Malaysia": 2200, "Mozambique": 4100, "Qatar": 1600, "Russia": 6300, "Saudi Arabia": 1700, "South Africa": 4800, "South Korea": 4300, "Thailand": 2000, "UAE": 1500, "US": 10200, "Vietnam": 2400},
    "Indonesia": {"India": 3200, "Australia": 2200, "China": 2100, "Japan": 2900, "South Korea": 2700, "US": 7800, "Brazil": 9500, "South Africa": 4900, "UAE": 3800, "Qatar": 3900, "Saudi Arabia": 4000, "Malaysia": 600, "Thailand": 900, "Vietnam": 1100, "Mozambique": 4200, "Russia": 3600},
    "Japan": {"India": 4500, "Australia": 4300, "China": 1100, "South Korea": 500, "US": 4800, "Brazil": 11500, "South Africa": 7500, "UAE": 5800, "Qatar": 5900, "Saudi Arabia": 6000, "Indonesia": 2900, "Malaysia": 2600, "Thailand": 2400, "Vietnam": 1900, "Mozambique": 6800, "Russia": 1100},
    "Malaysia": {"India": 2200, "Australia": 2800, "China": 1900, "Japan": 2600, "South Korea": 2400, "US": 8200, "Brazil": 9200, "South Africa": 4600, "UAE": 3300, "Qatar": 3400, "Saudi Arabia": 3500, "Indonesia": 600, "Thailand": 600, "Vietnam": 800, "Mozambique": 3900, "Russia": 3300},
    "Mozambique": {"India": 4100, "Australia": 5200, "Brazil": 4800, "China": 6100, "Indonesia": 4200, "Japan": 6800, "Malaysia": 3900, "Qatar": 3100, "Russia": 7200, "Saudi Arabia": 3000, "South Africa": 1100, "South Korea": 6600, "Thailand": 3800, "UAE": 3100, "US": 7600, "Vietnam": 4200},
    "Qatar": {"India": 1600, "Australia": 6300, "Brazil": 7300, "China": 5200, "Indonesia": 3900, "Japan": 5900, "Malaysia": 3400, "Mozambique": 3100, "Russia": 4800, "Saudi Arabia": 300, "South Africa": 4100, "South Korea": 5700, "Thailand": 3100, "UAE": 300, "US": 8900, "Vietnam": 3500},
    "Russia": {"India": 6300, "Australia": 5300, "Brazil": 9800, "China": 1500, "Indonesia": 3600, "Japan": 1100, "Malaysia": 3300, "Mozambique": 7200, "Qatar": 4800, "Saudi Arabia": 4900, "South Africa": 7900, "South Korea": 900, "Thailand": 3100, "UAE": 4700, "US": 5200, "Vietnam": 2600},
    "Saudi Arabia": {"India": 1700, "Australia": 6400, "Brazil": 7400, "China": 5300, "Indonesia": 4000, "Japan": 6000, "Malaysia": 3500, "Mozambique": 3000, "Qatar": 300, "Russia": 4900, "South Africa": 4000, "South Korea": 5800, "Thailand": 3200, "UAE": 400, "US": 8800, "Vietnam": 3600},
    "South Africa": {"India": 4800, "Australia": 5900, "Brazil": 3300, "China": 6800, "Indonesia": 4900, "Japan": 7500, "Malaysia": 4600, "Mozambique": 1100, "Qatar": 4100, "Russia": 7900, "Saudi Arabia": 4000, "South Korea": 7300, "Thailand": 4500, "UAE": 4000, "US": 6700, "Vietnam": 4900},
    "South Korea": {"India": 4300, "Australia": 4100, "China": 800, "Japan": 500, "US": 5000, "Brazil": 11200, "South Africa": 7300, "UAE": 5700, "Qatar": 5700, "Saudi Arabia": 5800, "Indonesia": 2700, "Malaysia": 2400, "Thailand": 2200, "Vietnam": 1700, "Mozambique": 6600, "Russia": 900},
    "Thailand": {"India": 2000, "Australia": 3100, "China": 1600, "Japan": 2400, "South Korea": 2200, "US": 8000, "Brazil": 9400, "South Africa": 4500, "UAE": 3100, "Qatar": 3100, "Saudi Arabia": 3200, "Indonesia": 900, "Malaysia": 600, "Mozambique": 3800, "Russia": 3100, "Vietnam": 500},
    "UAE": {"India": 1500, "Australia": 6200, "Brazil": 7200, "China": 5100, "Indonesia": 3800, "Japan": 5800, "Malaysia": 3300, "Mozambique": 3100, "Qatar": 300, "Russia": 4700, "Saudi Arabia": 400, "South Africa": 4000, "South Korea": 5700, "Thailand": 3100, "US": 8800, "Vietnam": 3500},
    "US": {"India": 10200, "Australia": 7500, "Brazil": 4500, "China": 5800, "Indonesia": 7800, "Japan": 4800, "Malaysia": 8200, "Mozambique": 7600, "Qatar": 8900, "Russia": 5200, "Saudi Arabia": 8800, "South Africa": 6700, "South Korea": 5000, "Thailand": 8000, "UAE": 8800, "Vietnam": 7900},
    "Vietnam": {"India": 2400, "Australia": 3300, "China": 1200, "Japan": 1900, "South Korea": 1700, "US": 7900, "Brazil": 9800, "South Africa": 4900, "UAE": 3500, "Qatar": 3500, "Saudi Arabia": 3600, "Indonesia": 1100, "Malaysia": 800, "Mozambique": 4200, "Russia": 2600, "Thailand": 500},
}

SAILING_DISTANCES_NM: dict[str, dict[str, int]] = {
    "Australia": {
        "Paradip": 5820, "Vizag": 5650, "Gangavaram": 5640, "Gopalpur": 5750,
        "Dhamra": 5850, "Sagar-Sandheads": 5950, "Haldia": 5970,
    },
    "US": {
        "Paradip": 10200, "Vizag": 10050, "Gangavaram": 10040, "Gopalpur": 10150,
        "Dhamra": 10250, "Sagar-Sandheads": 10350, "Haldia": 10370,
    },
    "Mozambique": {
        "Paradip": 4100, "Vizag": 3950, "Gangavaram": 3940, "Gopalpur": 4050,
        "Dhamra": 4130, "Sagar-Sandheads": 4250, "Haldia": 4270,
    },
    "Indonesia": {
        "Paradip": 3200, "Vizag": 3100, "Gangavaram": 3090, "Gopalpur": 3150,
        "Dhamra": 3230, "Sagar-Sandheads": 3350, "Haldia": 3370,
    },
    "Russia": {
        "Paradip": 6300, "Vizag": 6150, "Gangavaram": 6140, "Gopalpur": 6250,
        "Dhamra": 6330, "Sagar-Sandheads": 6450, "Haldia": 6470,
    },
    "South Africa": {
        "Paradip": 4800, "Vizag": 4650, "Gangavaram": 4640, "Gopalpur": 4750,
        "Dhamra": 4830, "Sagar-Sandheads": 4950, "Haldia": 4970,
    },
}


def get_sailing_distance(origin_country: str, dest_country: str = "India", dest_port: str = "Paradip") -> int:
    """Return distance in NM between origin and destination."""
    if dest_country == "India" and origin_country in SAILING_DISTANCES_NM:
        if dest_port in SAILING_DISTANCES_NM[origin_country]:
            return SAILING_DISTANCES_NM[origin_country][dest_port]
    if origin_country in COUNTRY_DISTANCE_MATRIX and dest_country in COUNTRY_DISTANCE_MATRIX[origin_country]:
        return COUNTRY_DISTANCE_MATRIX[origin_country][dest_country]
    if origin_country == dest_country:
        return 600
    return 4500

# Legacy PORT_LIMITS kept for backward compatibility (country level)
PORT_LIMITS = {country: {
    "max_loa_m": max(p["max_loa_m"] for p in ports.values()),
    "max_beam_m": max(p["max_beam_m"] for p in ports.values()),
    "max_draft_m": max(p["max_draft_m"] for p in ports.values()),
    "handling_tpd": max(p["handling_tpd"] for p in ports.values()),
    "annual_capacity_mt": 60,
} for country, ports in ORIGIN_PORTS.items()}

# Also add Indian port as a "country" entry for backward compatibility
PORT_LIMITS["India"] = {
    "max_loa_m": max(p["max_loa_m"] for p in INDIAN_EAST_COAST_PORTS.values()),
    "max_beam_m": max(p["max_beam_m"] for p in INDIAN_EAST_COAST_PORTS.values()),
    "max_draft_m": max(p["max_draft_m"] for p in INDIAN_EAST_COAST_PORTS.values()),
    "handling_tpd": max(p["handling_tpd"] for p in INDIAN_EAST_COAST_PORTS.values()),
    "annual_capacity_mt": 120,
}


# ---------------------------------------------------------------------------
# Pipeline result dataclass
# ---------------------------------------------------------------------------
@dataclass
class PipelineResult:
    df: pd.DataFrame
    summary: dict[str, Any]
    cleaned_df: pd.DataFrame
    features_df: pd.DataFrame
    model: RandomForestRegressor
    metrics: dict[str, float]
    forecast: pd.DataFrame
    recommendations: pd.DataFrame
    alerts: list[str]


# ---------------------------------------------------------------------------
# Column normalization
# ---------------------------------------------------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "origin": "origin_country",
        "destination": "destination_country",
        "origincountry": "origin_country",
        "destinationcountry": "destination_country",
        "vessel": "vessel_type",
        "vesseltype": "vessel_type",
        "rate": "rate_usd_per_ton",
        "rateusd": "rate_usd_per_ton",
        "freightrate": "rate_usd_per_ton",
        "date": "shipment_date",
        "shipmentdate": "shipment_date",
        "cargo": "cargo_tonnes",
        "cargotonnes": "cargo_tonnes",
        "tonnes": "cargo_tonnes",
        "origin_port": "origin_port",
        "destination_port": "destination_port",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


def read_dataset(file_obj=None) -> pd.DataFrame:
    if file_obj is not None:
        return normalize_columns(pd.read_csv(file_obj))
    return create_demo_dataset()


# ---------------------------------------------------------------------------
# Realistic synthetic dataset generator
# ---------------------------------------------------------------------------
def create_demo_dataset() -> pd.DataFrame:
    """Generate a realistic synthetic freight dataset reflecting actual trade dynamics.

    Models:
    - Trade-lane specific rates proportional to sailing distance + vessel cost
    - Indian power sector coal demand cycles (peaks: Apr-Jun pre-monsoon, Oct-Dec winter)
    - Monsoon congestion at East Coast ports (Jun-Sep)
    - Newcastle coal benchmark price correlation
    - Multi-year freight market cycles (boom/trough)
    - Vessel supply tightness premiums
    """
    rng = np.random.default_rng(42)
    rows = []
    dates = pd.date_range("2020-01-01", periods=60, freq="MS")  # 5 years monthly

    # Base coal price trajectory (indexed, 100 = baseline)
    coal_price_base = 100.0

    for date in dates:
        month = date.month
        year_offset = (date.year - 2020) + date.month / 12.0

        # --- Global market factors ---
        # Multi-year freight cycle (3-4 year super-cycle)
        market_cycle = 0.15 * np.sin(2 * np.pi * year_offset / 3.5)

        # Coal price evolution (uptrend 2020-2022, correction 2023, recovery 2024)
        coal_trend = coal_price_base + 40 * np.sin(2 * np.pi * year_offset / 4.0 - 0.5) + 8 * year_offset
        coal_index = coal_trend + rng.normal(0, 5)

        # Indian coal demand seasonality (power sector)
        # Peaks: Apr-Jun (pre-monsoon heat), Oct-Dec (winter industrial)
        demand_seasonality = (
            0.12 * np.sin(2 * np.pi * (month - 4) / 12)  # pre-monsoon peak
            + 0.08 * np.sin(2 * np.pi * (month - 11) / 6)  # winter peak
        )

        # Monsoon congestion factor for Indian East Coast (Jun-Sep)
        monsoon_congestion = 0.0
        if month in (6, 7, 8, 9):
            monsoon_congestion = 0.08 * (1.0 + 0.5 * np.sin(np.pi * (month - 6) / 3))

        for origin_country, origin_ports in ORIGIN_PORTS.items():
            for origin_port_name, origin_port_info in origin_ports.items():
                for dest_port_name, dest_port_info in INDIAN_EAST_COAST_PORTS.items():
                    distances = SAILING_DISTANCES_NM.get(origin_country, {})
                    distance_nm = distances.get(dest_port_name, 5000)

                    for vessel in VESSEL_CATALOG:
                        # --- Port feasibility check (skip infeasible combos) ---
                        if (vessel["loa_m"] > origin_port_info["max_loa_m"]
                                or vessel["beam_m"] > origin_port_info.get("max_beam_m", 99)
                                or vessel["draft_m"] > origin_port_info["max_draft_m"]):
                            continue
                        if (vessel["loa_m"] > dest_port_info["max_loa_m"]
                                or vessel["beam_m"] > dest_port_info["max_beam_m"]
                                or vessel["draft_m"] > dest_port_info["max_draft_m"]):
                            continue

                        # --- Rate computation ---
                        # Base rate from distance ($/ton, roughly $0.003-0.005/NM/ton)
                        distance_component = 0.0035 * distance_nm / 1000  # normalized

                        # Vessel size premium (larger = cheaper per ton)
                        size_efficiency = 1.0 - 0.3 * (vessel["dwt"] / 160000)

                        # Operating cost component
                        voyage_days = distance_nm / (vessel["speed_knots"] * 24)
                        daily_cost_per_ton = vessel["daily_cost_usd"] / vessel["dwt"]
                        ops_component = daily_cost_per_ton * voyage_days

                        # Assemble rate
                        base_rate = (
                            8.0                           # minimum base
                            + distance_component * 12     # distance contribution
                            + size_efficiency * 4          # vessel size effect
                            + ops_component * 100          # ops cost contribution
                            + coal_index * 0.04            # commodity price link
                            + market_cycle * 5             # market cycle
                            + demand_seasonality * 3       # seasonal demand
                            + monsoon_congestion * 4       # monsoon disruption
                        )

                        # Port-specific congestion noise
                        port_congestion = 1.0 + monsoon_congestion + rng.normal(0, 0.15)

                        # Final rate with noise
                        rate = base_rate + rng.normal(0, 0.6)
                        rate = max(rate, 5.0)  # floor

                        cargo = int(vessel["dwt"] * rng.uniform(0.65, 0.95))

                        rows.append({
                            "shipment_date": date,
                            "origin_country": origin_country,
                            "origin_port": origin_port_name,
                            "destination_country": "India",
                            "destination_port": dest_port_name,
                            "vessel_type": vessel["vessel_type"],
                            "cargo_tonnes": cargo,
                            "congestion_index": round(port_congestion, 3),
                            "commodity_index": round(coal_index, 2),
                            "demand_index": round(100 + demand_seasonality * 50, 2),
                            "distance_nm": distance_nm,
                            "rate_usd_per_ton": round(rate, 2),
                        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dataset understanding
# ---------------------------------------------------------------------------
def understand_dataset(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "nulls": df.isna().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "date_min": df["shipment_date"].min() if "shipment_date" in df.columns else None,
        "date_max": df["shipment_date"].max() if "shipment_date" in df.columns else None,
        "origin_count": df["origin_country"].nunique() if "origin_country" in df.columns else 0,
        "destination_count": df["destination_port"].nunique() if "destination_port" in df.columns else (
            df["destination_country"].nunique() if "destination_country" in df.columns else 0
        ),
        "vessel_types": sorted(df["vessel_type"].unique().tolist()) if "vessel_type" in df.columns else [],
        "origin_ports": sorted(df["origin_port"].unique().tolist()) if "origin_port" in df.columns else [],
        "destination_ports": sorted(df["destination_port"].unique().tolist()) if "destination_port" in df.columns else [],
    }


# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------
def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = normalize_columns(cleaned)

    for column in ["shipment_date", "origin_country", "destination_country", "vessel_type",
                    "origin_port", "destination_port"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype(str).str.strip()

    if "shipment_date" in cleaned.columns:
        cleaned["shipment_date"] = pd.to_datetime(cleaned["shipment_date"], errors="coerce")
        cleaned = cleaned.dropna(subset=["shipment_date"])

    if "rate_usd_per_ton" in cleaned.columns:
        cleaned["rate_usd_per_ton"] = pd.to_numeric(cleaned["rate_usd_per_ton"], errors="coerce")
        cleaned = cleaned.dropna(subset=["rate_usd_per_ton"])

    if "cargo_tonnes" in cleaned.columns:
        cleaned["cargo_tonnes"] = pd.to_numeric(cleaned["cargo_tonnes"], errors="coerce")

    for col in ["congestion_index", "commodity_index", "demand_index", "distance_nm"]:
        if col in cleaned.columns:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    return cleaned


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    engineered = df.copy()

    if "shipment_date" in engineered.columns:
        engineered["month"] = engineered["shipment_date"].dt.month
        engineered["year"] = engineered["shipment_date"].dt.year
        engineered["month_sin"] = np.sin(2 * np.pi * engineered["month"] / 12)
        engineered["month_cos"] = np.cos(2 * np.pi * engineered["month"] / 12)
        engineered["is_peak_season"] = engineered["month"].isin([10, 11, 12, 1, 2, 4, 5]).astype(int)
        engineered["is_monsoon"] = engineered["month"].isin([6, 7, 8, 9]).astype(int)

    # Origin country one-hot
    for country in ORIGIN_COUNTRY_LIST:
        engineered[f"origin_{country}"] = (engineered["origin_country"] == country).astype(int)

    # Destination port one-hot
    for port in INDIAN_PORT_LIST:
        engineered[f"dest_{port}"] = (engineered.get("destination_port", "") == port).astype(int)

    # Vessel type one-hot
    for vessel in VESSEL_TYPE_LIST:
        engineered[f"vessel_{vessel}"] = (engineered["vessel_type"] == vessel).astype(int)

    # Cargo band
    if "cargo_tonnes" in engineered.columns:
        engineered["cargo_band"] = pd.qcut(
            engineered["cargo_tonnes"], 5, labels=False, duplicates="drop"
        )

    # Distance feature
    if "distance_nm" in engineered.columns:
        engineered["distance_nm"] = pd.to_numeric(engineered["distance_nm"], errors="coerce").fillna(5000)

    # Congestion features
    if "congestion_index" in engineered.columns:
        engineered["congestion_index"] = pd.to_numeric(
            engineered["congestion_index"], errors="coerce"
        ).fillna(1.0)

    if "commodity_index" in engineered.columns:
        engineered["commodity_index"] = pd.to_numeric(
            engineered["commodity_index"], errors="coerce"
        ).fillna(100.0)

    if "demand_index" in engineered.columns:
        engineered["demand_index"] = pd.to_numeric(
            engineered["demand_index"], errors="coerce"
        ).fillna(100.0)

    return engineered


# ---------------------------------------------------------------------------
# ML model training
# ---------------------------------------------------------------------------
def train_ml_model(df: pd.DataFrame, model_type: str = "tft"):
    feature_df = df.copy()
    target = "rate_usd_per_ton"
    exclude = {
        target, "shipment_date", "origin_country", "destination_country",
        "vessel_type", "origin_port", "destination_port",
    }
    feature_columns = [col for col in feature_df.columns if col not in exclude]

    # Chronological Time-Series Validation Split (Past -> Train, Future -> Test)
    if "shipment_date" in feature_df.columns:
        feature_df = feature_df.sort_values("shipment_date").reset_index(drop=True)
        X = feature_df[feature_columns].apply(pd.to_numeric, errors="coerce").fillna(0)
        y = feature_df[target]

    split_idx = int(len(feature_df) * 0.8)
    X_train, y_train = X.iloc[:split_idx], y.iloc[:split_idx]
    X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]

    if model_type.lower() == "tft":
        model = TemporalFusionTransformerRegressor(hidden_dim=64, num_heads=4, max_epochs=100, random_state=42)
    elif model_type.lower() == "gnn":
        model = GraphNeuralNetworkRegressor(hidden_dim=64, max_epochs=100, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_test, predictions))),
        "r2": float(r2_score(y_test, predictions)),
    }
    return model, metrics, X_test, y_test


# ---------------------------------------------------------------------------
# Freight rate forecasting
# ---------------------------------------------------------------------------
def forecast_rates(
    model,
    origin_country: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    months: int = 6,
    feature_columns: list[str] | None = None,
    origin_port: str | None = None,
    destination_country: str = "India",
):
    """Forecast freight rates for upcoming months using the trained model."""
    future_rows = []
    start_date = pd.Timestamp.today().normalize().to_period("M").to_timestamp() + pd.offsets.MonthBegin(1)

    distances = SAILING_DISTANCES_NM.get(origin_country, {})
    distance_nm = distances.get(destination_port, 5000)

    for idx in range(months):
        future_date = start_date + pd.DateOffset(months=idx)
        month = future_date.month
        month_factor = 2 * np.pi * (month - 1) / 12
        is_monsoon = int(month in (6, 7, 8, 9))

        congestion = 1.0 + (0.15 if is_monsoon else 0.0) + 0.08 * np.sin(month_factor + 1.2)
        demand = 100 + 6 * np.sin(2 * np.pi * (month - 4) / 12) + 4 * np.sin(2 * np.pi * (month - 11) / 6)
        coal_index = 130 + 10 * np.sin(month_factor - 0.8)

        future_rows.append({
            "shipment_date": future_date,
            "origin_country": origin_country,
            "origin_port": origin_port or "",
            "destination_country": destination_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "congestion_index": congestion,
            "commodity_index": coal_index,
            "demand_index": demand,
            "distance_nm": distance_nm,
            "rate_usd_per_ton": 0,
            "month": month,
            "year": future_date.year,
            "month_sin": np.sin(2 * np.pi * month / 12),
            "month_cos": np.cos(2 * np.pi * month / 12),
            "is_peak_season": int(month in (10, 11, 12, 1, 2, 4, 5)),
            "is_monsoon": is_monsoon,
            "cargo_band": 2,
        })

    forecast_df = pd.DataFrame(future_rows)

    # One-hot encode
    for country in ORIGIN_COUNTRY_LIST:
        forecast_df[f"origin_{country}"] = (forecast_df["origin_country"] == country).astype(int)
    for port in INDIAN_PORT_LIST:
        forecast_df[f"dest_{port}"] = (forecast_df["destination_port"] == port).astype(int)
    for v in VESSEL_TYPE_LIST:
        forecast_df[f"vessel_{v}"] = (forecast_df["vessel_type"] == v).astype(int)

    if feature_columns is None:
        feature_columns = getattr(model, "feature_names_in_", None)
    if feature_columns is None:
        exclude = {"shipment_date", "origin_country", "destination_country",
                    "vessel_type", "origin_port", "destination_port", "rate_usd_per_ton"}
        feature_columns = [c for c in forecast_df.columns if c not in exclude]

    for column in feature_columns:
        if column not in forecast_df.columns:
            forecast_df[column] = 0.0

    prediction_data = forecast_df.reindex(columns=feature_columns).apply(pd.to_numeric, errors="coerce").fillna(0)
    prediction_values = prediction_data.values  # numpy array to avoid sklearn feature-name warnings

    # Point prediction
    forecast_df["forecast_rate"] = model.predict(prediction_values)

    # Confidence bounds via tree variance (if RandomForest)
    if hasattr(model, "estimators_"):
        tree_preds = np.array([t.predict(prediction_values) for t in model.estimators_])
        forecast_df["rate_std"] = tree_preds.std(axis=0)
        forecast_df["rate_lower"] = forecast_df["forecast_rate"] - 1.96 * forecast_df["rate_std"]
        forecast_df["rate_upper"] = forecast_df["forecast_rate"] + 1.96 * forecast_df["rate_std"]
    else:
        forecast_df["rate_std"] = 0.0
        forecast_df["rate_lower"] = forecast_df["forecast_rate"]
        forecast_df["rate_upper"] = forecast_df["forecast_rate"]

    result = forecast_df[["shipment_date", "forecast_rate", "rate_lower", "rate_upper", "rate_std"]].rename(
        columns={"forecast_rate": "rate_usd_per_ton"}
    )
    return result


# ---------------------------------------------------------------------------
# Vessel recommendation (port-aware)
# ---------------------------------------------------------------------------
def recommend_vessels(
    origin_country: str,
    destination_port: str,
    cargo_tonnes: float,
    origin_port: str | None = None,
) -> pd.DataFrame:
    """Recommend feasible vessel types given port infrastructure constraints at both ends."""
    dest_info = INDIAN_EAST_COAST_PORTS.get(destination_port)
    if dest_info is None:
        # Fallback: try country-level
        dest_info = PORT_LIMITS.get(destination_port)
    if dest_info is None:
        return pd.DataFrame()

    # Origin port constraints (if specified)
    origin_info = None
    if origin_port:
        origin_info = get_origin_port_info(origin_country, origin_port)

    distances = SAILING_DISTANCES_NM.get(origin_country, {})
    distance_nm = distances.get(destination_port, 5000)

    options = []
    for vessel in VESSEL_CATALOG:
        # Check destination port constraints
        if (vessel["loa_m"] > dest_info["max_loa_m"]
                or vessel["beam_m"] > dest_info["max_beam_m"]
                or vessel["draft_m"] > dest_info["max_draft_m"]):
            continue

        # Check origin port constraints (if known)
        if origin_info is not None:
            if (vessel["loa_m"] > origin_info["max_loa_m"]
                    or vessel["draft_m"] > origin_info["max_draft_m"]):
                continue

        # Voyage economics
        voyage_days = round(distance_nm / (vessel["speed_knots"] * 24), 1)
        load_days = round(cargo_tonnes / vessel["load_tpd"], 1)
        unload_days = round(cargo_tonnes / dest_info["handling_tpd"], 1)
        total_days = voyage_days + load_days + unload_days + 2  # +2 for port entry/exit
        voyage_cost = vessel["daily_cost_usd"] * total_days
        fuel_cost = vessel["fuel_mt_per_day"] * voyage_days * 600  # ~$600/MT bunker fuel
        total_cost = voyage_cost + fuel_cost

        num_voyages = max(1, int(cargo_tonnes / vessel["dwt"]) + (1 if cargo_tonnes % vessel["dwt"] > 0 else 0))

        options.append({
            "vessel_type": vessel["vessel_type"],
            "dwt": vessel["dwt"],
            "loa_m": vessel["loa_m"],
            "beam_m": vessel["beam_m"],
            "draft_m": vessel["draft_m"],
            "load_tpd": vessel["load_tpd"],
            "daily_cost_usd": vessel["daily_cost_usd"],
            "voyage_days": voyage_days,
            "load_days": load_days,
            "unload_days": unload_days,
            "total_days": total_days,
            "num_voyages": num_voyages,
            "voyage_cost_usd": round(total_cost, 0),
            "cost_per_tonne": round(total_cost / cargo_tonnes, 2) if cargo_tonnes > 0 else 0,
            "distance_nm": distance_nm,
        })

    return pd.DataFrame(options)


# ---------------------------------------------------------------------------
# Risk alerts (enhanced)
# ---------------------------------------------------------------------------
def risk_alerts(
    forecast_df: pd.DataFrame,
    route_context: dict[str, Any],
) -> list[str]:
    """Generate categorized risk alerts based on forecast and route context."""
    alerts: list[str] = []
    rates = forecast_df["rate_usd_per_ton"]
    avg_rate = float(rates.mean())

    # --- Volatility ---
    if "rate_std" in forecast_df.columns:
        avg_std = float(forecast_df["rate_std"].mean())
        if avg_std > 1.5:
            alerts.append(f"⚠️ HIGH VOLATILITY: Forecast uncertainty is elevated (±${avg_std:.2f}/ton). Consider locking in a term contract to hedge against rate swings.")

    # Rate trend
    if len(rates) >= 2:
        trend = float(rates.iloc[-1] - rates.iloc[0])
        if trend > 2.0:
            alerts.append(f"📈 RISING RATES: Rates are forecast to increase by ${trend:.2f}/ton over the horizon. Earlier market entry is recommended.")
        elif trend < -2.0:
            alerts.append(f"📉 FALLING RATES: Rates are forecast to decrease by ${abs(trend):.2f}/ton. Deferring spot bookings may yield savings.")

    # --- Cargo size ---
    cargo = route_context.get("cargo_tonnes", 0)
    if cargo > 100000:
        alerts.append("📦 LARGE CARGO: Cargo exceeds 100,000 tonnes. Verify berth scheduling and consider split-shipment to reduce port congestion risk.")

    # --- Monsoon risk ---
    dest_port = route_context.get("destination_port", "")
    if dest_port in ("Gopalpur", "Sagar-Sandheads", "Haldia"):
        alerts.append(f"🌧️ MONSOON EXPOSURE: {dest_port} is highly vulnerable to monsoon disruption (Jun-Sep). Consider alternative discharge ports or schedule outside monsoon window.")

    # --- Draft-restricted ports ---
    if dest_port in ("Sagar-Sandheads", "Haldia"):
        alerts.append(f"⚓ DRAFT RESTRICTION: {dest_port} has severe draft limitations (≤13m). Only Handysize/Supramax vessels are feasible. Partial loading may be required for larger vessels.")

    # --- High-rate environment ---
    if avg_rate > 30:
        alerts.append(f"💰 ELEVATED RATES: Average forecast rate is ${avg_rate:.2f}/ton, above typical market levels. Evaluate short-term contracts vs. spot exposure carefully.")

    # --- Origin concentration ---
    origin = route_context.get("origin_country", "")
    if origin in ("Australia",):
        alerts.append("🌏 ORIGIN RISK: Heavy reliance on Australian coal exports. Monitor cyclone season (Nov-Apr) and port disruption at Newcastle/Hay Point.")
    elif origin in ("Russia",):
        alerts.append("🌍 GEOPOLITICAL RISK: Russian-origin cargo may face sanctions-related shipping constraints and insurance limitations.")
    elif origin in ("Mozambique",):
        alerts.append("🌍 LOGISTICS RISK: Mozambique ports have limited handling capacity. Beira port is particularly draft-restricted (≤12m).")

    if not alerts:
        alerts.append("✅ No immediate risk thresholds breached. Market conditions appear favorable for current booking parameters.")

    return alerts


# ---------------------------------------------------------------------------
# Full pipeline runner
# ---------------------------------------------------------------------------
def run_pipeline(df: pd.DataFrame):
    cleaned = clean_dataset(df)
    summary = understand_dataset(cleaned)
    features = engineer_features(cleaned)
    model, metrics, _, _ = train_ml_model(features)
    forecast = forecast_rates(model, "Australia", "Paradip", "Supramax", 50000, months=6)
    recommendations = recommend_vessels("Australia", "Paradip", 50000)
    alerts = risk_alerts(forecast, {"cargo_tonnes": 50000, "destination_port": "Paradip", "origin_country": "Australia"})
    return PipelineResult(
        df=df,
        summary=summary,
        cleaned_df=cleaned,
        features_df=features,
        model=model,
        metrics=metrics,
        forecast=forecast,
        recommendations=recommendations,
        alerts=alerts,
    )


# ---------------------------------------------------------------------------
# Shipment Date Feasibility & 5-Day Approximate Alternative Date Recommendation
# ---------------------------------------------------------------------------
def evaluate_shipment_date(
    target_date_str: str,
    origin_country: str,
    origin_port: str | None = None,
    destination_country: str = "India",
    destination_port: str = "Paradip",
    vessel_type: str = "Supramax",
    cargo_tonnes: float = 50000,
    model=None,
    feature_columns=None,
) -> dict[str, Any]:
    """Evaluate whether a given shipment date is optimal/correct and generate 5 approximate alternative dates if risky/costly."""
    try:
        target_dt = pd.to_datetime(target_date_str).normalize()
    except Exception:
        target_dt = pd.Timestamp.today().normalize()

    month = target_dt.month
    day_of_year = target_dt.dayofyear

    # 1. Weather / Monsoon risk assessment
    is_monsoon = (month in (6, 7, 8, 9))
    monsoon_vulnerable_ports = ("Gopalpur", "Sagar-Sandheads", "Haldia", "Paradip")
    high_monsoon_risk = is_monsoon and (destination_port in monsoon_vulnerable_ports)

    # 2. Estimate rate for target date
    distance_nm = get_sailing_distance(origin_country, destination_country, destination_port)
    base_rate = 25.0 + (distance_nm / 1000.0) * 2.8
    month_sin = np.sin(2 * np.pi * month / 12)
    month_cos = np.cos(2 * np.pi * month / 12)

    if model is not None and feature_columns is not None:
        try:
            row_dict = {col: 0.0 for col in feature_columns}
            row_dict.update({
                "cargo_tonnes": cargo_tonnes,
                "distance_nm": distance_nm,
                "month": month,
                "year": target_dt.year,
                "month_sin": month_sin,
                "month_cos": month_cos,
                "is_peak_season": int(month in (10, 11, 12, 1, 2, 4, 5)),
                "is_monsoon": int(is_monsoon),
                "cargo_band": 2,
            })
            sample_df = pd.DataFrame([row_dict])[feature_columns]
            pred = float(model.predict(sample_df)[0])
            if pred > 0:
                base_rate = pred
        except Exception:
            pass

    daily_factor = 1.0 + 0.05 * np.sin(2 * np.pi * day_of_year / 15.0) + (0.12 if high_monsoon_risk else 0.0)
    target_rate = round(base_rate * daily_factor, 2)
    total_freight_usd = round(target_rate * cargo_tonnes, 2)

    # Determine status & risk factors
    risk_factors = []
    if high_monsoon_risk:
        risk_factors.append(f"🌧️ Peak Monsoon Risk: {destination_port} experiences severe swells and berthing delays (Jun-Sep).")
    elif is_monsoon:
        risk_factors.append(f"🌦️ Seasonal Monsoon Window: Weather disruption possible at {destination_port}.")

    if month in (11, 12, 1):
        risk_factors.append("📈 Winter Peak Season: High seasonal demand elevates spot freight rates.")

    is_optimal = len(risk_factors) == 0 and daily_factor <= 1.02
    status = "OPTIMAL" if is_optimal else ("HIGH_RISK" if high_monsoon_risk else "MODERATE_RISK")

    # 3. Generate 5 approximate alternative dates around target_date
    candidate_offsets = [-14, -10, -7, -4, -2, 3, 5, 8, 12, 15]
    candidates = []

    for offset in candidate_offsets:
        alt_dt = target_dt + pd.Timedelta(days=offset)
        alt_month = alt_dt.month
        alt_day_year = alt_dt.dayofyear
        alt_monsoon = (alt_month in (6, 7, 8, 9)) and (destination_port in monsoon_vulnerable_ports)

        alt_daily_factor = 1.0 + 0.05 * np.sin(2 * np.pi * alt_day_year / 15.0) + (0.12 if alt_monsoon else 0.0)
        alt_rate = round(base_rate * alt_daily_factor, 2)
        savings_usd = round((target_rate - alt_rate) * cargo_tonnes, 2)

        if alt_monsoon:
            alt_risk = "HIGH"
            reason = "Weather disruption risk; consider post-monsoon dates."
        elif offset < 0 and savings_usd > 0:
            alt_risk = "LOW"
            reason = f"Favorable pre-window dispatch. Saves ${savings_usd:,.0f} vs target date."
        elif offset > 0 and savings_usd > 0:
            alt_risk = "LOW"
            reason = f"Lower spot rate window. Saves ${savings_usd:,.0f} vs target date."
        elif not alt_monsoon:
            alt_risk = "LOW"
            reason = "Clear sailing window with optimal port berth availability."
        else:
            alt_risk = "MEDIUM"
            reason = "Moderate market conditions."

        candidates.append({
            "date": alt_dt.strftime("%Y-%m-%d"),
            "offset_days": f"{'+' if offset > 0 else ''}{offset} days",
            "estimated_rate": alt_rate,
            "savings_usd": max(0.0, savings_usd),
            "risk_level": alt_risk,
            "reason": reason,
        })

    candidates.sort(key=lambda x: (0 if x["risk_level"] == "LOW" else (1 if x["risk_level"] == "MEDIUM" else 2), -x["savings_usd"]))
    alternative_dates = candidates[:5]

    return {
        "target_date": target_dt.strftime("%Y-%m-%d"),
        "is_optimal": is_optimal,
        "status": status,
        "estimated_rate": target_rate,
        "total_freight_usd": total_freight_usd,
        "risk_factors": risk_factors if risk_factors else ["✅ No major weather or rate risks identified for selected shipment date."],
        "alternative_dates": alternative_dates,
    }
