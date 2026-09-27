"""API Client module for communicating with the Freight Forecasting FastAPI backend."""
from __future__ import annotations

import os
import pandas as pd
import requests
from typing import Any

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")



class DotDict(dict):
    """Dictionary subclass enabling attribute-style dot lookup."""

    def __getattr__(self, key: str) -> Any:
        try:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, DotDict):
                val = DotDict(val)
            return val
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class FreightAPIClient:
    def __init__(self, base_url: str = DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def check_health(self) -> DotDict:
        """Check connection health and model load status."""
        try:
            r = requests.get(self._url("/api/health"), timeout=5)
            if r.status_code == 200:
                return DotDict(r.json())
            return DotDict({"status": "error", "message": f"HTTP {r.status_code}"})
        except Exception as e:
            return DotDict({"status": "error", "message": str(e)})

    # --- Unified Shipment Processing ---
    def process_shipment(self, payload: dict[str, Any]) -> DotDict:
        """Call unified backend endpoint to process shipment data end-to-end."""
        try:
            r = requests.post(self._url("/api/process"), json=payload, timeout=20)
            r.raise_for_status()
            return DotDict(r.json())
        except Exception as e:
            return DotDict({"status": "error", "message": str(e)})

    # --- Ports & Data Catalog ---
    def get_origin_countries(self) -> list[str]:
        r = requests.get(self._url("/api/ports/origin-countries"), timeout=5)
        r.raise_for_status()
        return r.json().get("countries", [])

    def get_all_countries(self) -> list[str]:
        r = requests.get(self._url("/api/ports/all-countries"), timeout=5)
        r.raise_for_status()
        return r.json().get("countries", [])

    def get_ports_by_country(self, country: str) -> tuple[dict[str, Any], list[str]]:
        params = {"country": country}
        r = requests.get(self._url("/api/ports/by-country"), params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data.get("ports", {}), data.get("port_names", [])

    def get_origin_ports(self, country: str | None = None) -> dict[str, Any]:
        params = {"country": country} if country else {}
        r = requests.get(self._url("/api/ports/origin"), params=params, timeout=5)
        r.raise_for_status()
        res = r.json()
        return res.get("ports", {}) if not country else {country: res.get("ports", [])}

    def get_indian_ports(self) -> tuple[dict[str, Any], list[str]]:
        r = requests.get(self._url("/api/ports/indian"), timeout=5)
        r.raise_for_status()
        data = r.json()
        return data.get("ports", {}), data.get("port_names", [])

    def get_distances(self) -> dict[str, dict[str, float]]:
        r = requests.get(self._url("/api/ports/distances"), timeout=5)
        r.raise_for_status()
        return r.json().get("distances", {})

    def get_vessel_catalog(self) -> list[dict[str, Any]]:
        r = requests.get(self._url("/api/ports/vessels"), timeout=5)
        r.raise_for_status()
        return r.json().get("vessels", [])

    # --- Forecast ---
    def get_forecast(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        months: int = 6,
        origin_port: str | None = None,
    ) -> pd.DataFrame:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "months": months,
            "origin_port": origin_port,
        }
        r = requests.post(self._url("/api/forecast"), json=payload, timeout=10)
        r.raise_for_status()
        records = r.json().get("forecast", [])
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        if "shipment_date" in df.columns:
            df["shipment_date"] = pd.to_datetime(df["shipment_date"])
        return df

    def compare_vessels(
        self,
        origin_country: str,
        destination_port: str,
        cargo_tonnes: float,
        months: int = 6,
    ) -> dict[str, pd.DataFrame]:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": "Supramax",
            "cargo_tonnes": cargo_tonnes,
            "months": months,
        }
        r = requests.post(self._url("/api/forecast/compare-vessels"), json=payload, timeout=10)
        r.raise_for_status()
        raw = r.json().get("vessel_forecasts", {})
        result = {}
        for vt, recs in raw.items():
            df = pd.DataFrame(recs)
            if "shipment_date" in df.columns:
                df["shipment_date"] = pd.to_datetime(df["shipment_date"])
            result[vt] = df
        return result

    def compare_routes(
        self,
        origin_country: str,
        vessel_type: str,
        cargo_tonnes: float,
        months: int = 6,
    ) -> dict[str, pd.DataFrame]:
        payload = {
            "origin_country": origin_country,
            "destination_port": "Paradip",
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "months": months,
        }
        r = requests.post(self._url("/api/forecast/compare-routes"), json=payload, timeout=10)
        r.raise_for_status()
        raw = r.json().get("route_forecasts", {})
        result = {}
        for port, recs in raw.items():
            df = pd.DataFrame(recs)
            if "shipment_date" in df.columns:
                df["shipment_date"] = pd.to_datetime(df["shipment_date"])
            result[port] = df
        return result

    def retrain_model(self) -> DotDict:
        r = requests.post(self._url("/api/forecast/retrain"), timeout=60)
        r.raise_for_status()
        return DotDict(r.json())

    def get_billing_statement(
        self,
        origin_country: str,
        origin_port: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        spot_rate_per_ton: float = 25.0,
        discount_pct: float = 0.0,
        tax_pct: float = 5.0,
        currency: str = "USD",
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "spot_rate_per_ton": spot_rate_per_ton,
            "discount_pct": discount_pct,
            "tax_pct": tax_pct,
            "currency": currency,
        }
        try:
            r = requests.post(self._url("/api/voyage/billing"), json=payload, timeout=10)
            r.raise_for_status()
            return DotDict(r.json())
        except Exception:
            return DotDict({})

    # --- Contracts ---
    def compare_contracts(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        voyages_per_year: int = 6,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "voyages_per_year": voyages_per_year,
        }
        r = requests.post(self._url("/api/contracts/compare"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json().get("contract", {}))

    def get_market_entry(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        forecast_months: int = 6,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "forecast_months": forecast_months,
        }
        r = requests.post(self._url("/api/contracts/market-entry"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json().get("signal", {}))

    def get_idle_analysis(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/contracts/idle-analysis"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json().get("idle", {}))

    def run_scenario(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        rate_change_pct: float,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "rate_change_pct": rate_change_pct,
        }
        r = requests.post(self._url("/api/contracts/scenario"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json().get("scenario", {}))

    # --- Vessels ---
    def recommend_vessels(
        self,
        origin_country: str,
        destination_port: str,
        cargo_tonnes: float,
        origin_port: str | None = None,
    ) -> pd.DataFrame:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "cargo_tonnes": cargo_tonnes,
            "origin_port": origin_port,
        }
        r = requests.post(self._url("/api/vessels/recommend"), json=payload, timeout=10)
        r.raise_for_status()
        recs = r.json().get("vessels", [])
        return pd.DataFrame(recs) if recs else pd.DataFrame()

    def get_feasibility_matrix(self) -> pd.DataFrame:
        r = requests.get(self._url("/api/vessels/feasibility-matrix"), timeout=5)
        r.raise_for_status()
        matrix = r.json().get("matrix", [])
        return pd.DataFrame(matrix) if matrix else pd.DataFrame()

    # --- Risk ---
    def get_risk_alerts(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        months: int = 6,
    ) -> list[str]:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "months": months,
        }
        r = requests.post(self._url("/api/risk/alerts"), json=payload, timeout=10)
        r.raise_for_status()
        return r.json().get("alerts", [])

    def evaluate_shipment_date(
        self,
        target_date: str,
        origin_country: str,
        origin_port: str | None = None,
        destination_country: str = "India",
        destination_port: str = "Paradip",
        vessel_type: str = "Supramax",
        cargo_tonnes: float = 50000,
    ) -> DotDict:
        payload = {
            "target_date": target_date,
            "origin_country": origin_country,
            "origin_port": origin_port,
            "destination_country": destination_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/risk/evaluate-date"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    def get_route_assessment(
        self,
        origin_country: str,
        vessel_type: str,
        cargo_tonnes: float,
    ) -> pd.DataFrame:
        payload = {
            "origin_country": origin_country,
            "destination_port": "Paradip",
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/risk/route-assessment"), json=payload, timeout=10)
        r.raise_for_status()
        data = r.json().get("assessment", [])
        return pd.DataFrame(data) if data else pd.DataFrame()

    def get_monsoon_calendar(self) -> pd.DataFrame:
        r = requests.get(self._url("/api/risk/monsoon"), timeout=5)
        r.raise_for_status()
        data = r.json().get("monsoon", [])
        return pd.DataFrame(data) if data else pd.DataFrame()

    # --- Voyage ---
    def get_voyage_cost(
        self,
        origin_country: str,
        origin_port: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
    ) -> DotDict | None:
        payload = {
            "origin_country": origin_country,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/voyage/cost"), json=payload, timeout=10)
        r.raise_for_status()
        raw = r.json().get("voyage")
        return DotDict(raw) if raw else None

    def compare_all_voyages(
        self,
        origin_country: str,
        origin_port: str,
        destination_port: str,
        cargo_tonnes: float,
    ) -> list[DotDict]:
        payload = {
            "origin_country": origin_country,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/voyage/compare-all"), json=payload, timeout=10)
        r.raise_for_status()
        voyages = r.json().get("voyages", [])
        return [DotDict(v) for v in voyages]

    # --- Web Scraper & Intelligence ---
    def get_live_scraped_indices(self) -> DotDict:
        r = requests.get(self._url("/api/scraper/live-indices"), timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    def scrape_custom_url(self, target_url: str) -> DotDict:
        payload = {"url": target_url}
        r = requests.post(self._url("/api/scraper/scrape-url"), json=payload, timeout=15)
        r.raise_for_status()
        return DotDict(r.json())

    def ingest_scraped_data(self, scraped_data: dict[str, Any]) -> DotDict:
        payload = {"scraped_data": scraped_data}
        r = requests.post(self._url("/api/scraper/ingest"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    # --- Linked List Voyage Navigator ---
    def build_route_linked_list(
        self,
        origin_country: str,
        origin_port: str,
        destination_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "origin_port": origin_port,
            "destination_country": destination_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
        }
        r = requests.post(self._url("/api/linked-list/build-route"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    def insert_route_node(
        self,
        target_node_id: str,
        new_node_title: str,
        location_name: str,
        country: str,
        vessel_type: str,
        distance_nm: float,
        cost_usd: float,
        current_nodes: list[dict[str, Any]],
    ) -> DotDict:
        payload = {
            "target_node_id": target_node_id,
            "new_node_title": new_node_title,
            "location_name": location_name,
            "country": country,
            "vessel_type": vessel_type,
            "distance_nm": distance_nm,
            "cost_usd": cost_usd,
            "current_nodes": current_nodes,
        }
        r = requests.post(self._url("/api/linked-list/insert-node"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    def remove_route_node(self, node_id: str, current_nodes: list[dict[str, Any]]) -> DotDict:
        payload = {"node_id": node_id, "current_nodes": current_nodes}
        r = requests.post(self._url("/api/linked-list/remove-node"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

    # --- Export Reports & Benchmarking ---
    def export_shipment_report(self, payload: dict[str, Any], fmt: str = "json") -> DotDict | str:
        body = {**payload, "format": fmt}
        r = requests.post(self._url("/api/reports/export"), json=body, timeout=30)
        r.raise_for_status()
        if fmt.lower() == "csv":
            return r.text
        return DotDict(r.json())

    def benchmark_scenarios(self, scenarios: list[dict[str, Any]]) -> DotDict:
        payload = {"scenarios": scenarios}
        r = requests.post(self._url("/api/contracts/benchmark"), json=payload, timeout=20)
        r.raise_for_status()
        return DotDict(r.json())

    def get_live_risk_matrix(
        self,
        origin_country: str,
        destination_port: str,
        vessel_type: str,
        cargo_tonnes: float,
        months: int = 6,
    ) -> DotDict:
        payload = {
            "origin_country": origin_country,
            "destination_port": destination_port,
            "vessel_type": vessel_type,
            "cargo_tonnes": cargo_tonnes,
            "months": months,
        }
        r = requests.post(self._url("/api/risk/live-alerts"), json=payload, timeout=10)
        r.raise_for_status()
        return DotDict(r.json())

