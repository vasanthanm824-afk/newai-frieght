"""Contracts router — strategy comparison, market entry, idle analysis."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.contract_optimizer import (
    analyze_idle_scenarios,
    analyze_market_entry,
    compare_contract_strategies,
    simulate_rate_scenario,
)
from ..state import get_feature_columns, get_model

router = APIRouter()


class ContractRequest(BaseModel):
    origin_country: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    voyages_per_year: int = 6
    forecast_months: int = 6


@router.post("/compare")
def compare_contracts(req: ContractRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    result = compare_contract_strategies(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, req.voyages_per_year, get_feature_columns(),
    )
    return {"contract": asdict(result)}


@router.post("/market-entry")
def market_entry(req: ContractRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    result = analyze_market_entry(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, req.forecast_months, get_feature_columns(),
    )
    return {"signal": asdict(result)}


@router.post("/idle-analysis")
def idle_analysis(req: ContractRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    result = analyze_idle_scenarios(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, get_feature_columns(),
    )
    return {"idle": asdict(result)}


class ScenarioRequest(BaseModel):
    origin_country: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    rate_change_pct: float


@router.post("/scenario")
def run_scenario(req: ScenarioRequest):
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}
    result = simulate_rate_scenario(
        model, req.origin_country, req.destination_port, req.vessel_type,
        req.cargo_tonnes, req.rate_change_pct, get_feature_columns(),
    )
    return {"scenario": result}


class SingleBenchmarkScenario(BaseModel):
    scenario_name: str
    origin_country: str = "Australia"
    destination_port: str = "Paradip"
    vessel_type: str = "Supramax"
    cargo_tonnes: float = 50000.0
    voyages_per_year: int = 6


class BenchmarkRequest(BaseModel):
    scenarios: list[SingleBenchmarkScenario]


@router.post("/benchmark")
def benchmark_scenarios(req: BenchmarkRequest):
    """Benchmark multiple shipment scenarios side-by-side."""
    model = get_model()
    if model is None:
        return {"error": "Model not loaded"}

    feature_cols = get_feature_columns()
    benchmarks = []
    
    for s in req.scenarios:
        strategy_res = compare_contract_strategies(
            model,
            s.origin_country,
            s.destination_port,
            s.vessel_type,
            s.cargo_tonnes,
            s.voyages_per_year,
            feature_cols,
        )
        entry_res = analyze_market_entry(
            model,
            s.origin_country,
            s.destination_port,
            s.vessel_type,
            s.cargo_tonnes,
            6,
            feature_cols,
        )
        
        benchmarks.append({
            "scenario_name": s.scenario_name,
            "origin_country": s.origin_country,
            "destination_port": s.destination_port,
            "vessel_type": s.vessel_type,
            "cargo_tonnes": s.cargo_tonnes,
            "recommended_strategy": strategy_res.recommended_strategy,
            "contract_rate_per_ton": strategy_res.long_term_avg_rate,
            "spot_rate_per_ton": strategy_res.spot_avg_rate,
            "annual_savings_vs_spot": strategy_res.savings_vs_spot,
            "market_entry_action": entry_res.action,
            "confidence": entry_res.confidence,
        })


    # Sort benchmarks by annual savings descending
    benchmarks.sort(key=lambda x: x.get("annual_savings_vs_spot", 0), reverse=True)
    best_option = benchmarks[0]["scenario_name"] if benchmarks else None

    return {
        "status": "success",
        "benchmark_count": len(benchmarks),
        "recommended_scenario": best_option,
        "results": benchmarks,
    }

