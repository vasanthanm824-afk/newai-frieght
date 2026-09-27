"""Contract Strategy Optimizer — spot vs. term contract comparison,
optimal market entry timing, and idle scenario management.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from freight_pipeline import (
    VESSEL_CATALOG,
    forecast_rates,
    recommend_vessels,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class MarketEntrySignal:
    """Recommendation on when to enter the market."""
    action: str                    # "BOOK NOW", "WAIT", "HEDGE"
    confidence: str                # "HIGH", "MEDIUM", "LOW"
    current_rate: float
    forecast_avg: float
    forecast_min: float
    forecast_min_month: str
    potential_savings_pct: float
    rationale: str


@dataclass
class ContractComparison:
    """Side-by-side comparison of spot vs. term contract strategies."""
    spot_total_cost: float
    spot_avg_rate: float
    spot_voyages: int
    short_term_total_cost: float    # 1-3 months
    short_term_avg_rate: float
    short_term_discount_pct: float
    mid_term_total_cost: float      # 3-6 months
    mid_term_avg_rate: float
    mid_term_discount_pct: float
    long_term_total_cost: float     # 6-12 months
    long_term_avg_rate: float
    long_term_discount_pct: float
    recommended_strategy: str
    savings_vs_spot: float


@dataclass
class IdleScenario:
    """Analysis of potential idle periods and mitigation strategies."""
    low_demand_months: list[str] = field(default_factory=list)
    estimated_idle_days: float = 0.0
    idle_cost_usd: float = 0.0
    repositioning_suggestions: list[str] = field(default_factory=list)
    backhaul_opportunities: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Optimal market entry timing
# ---------------------------------------------------------------------------
def analyze_market_entry(
    model,
    origin_country: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    forecast_months: int = 6,
    feature_columns: list[str] | None = None,
) -> MarketEntrySignal:
    """Determine whether to book now, wait, or hedge based on forecast trajectory."""
    forecast = forecast_rates(
        model, origin_country, destination_port, vessel_type,
        cargo_tonnes, months=forecast_months, feature_columns=feature_columns,
    )

    rates = forecast["rate_usd_per_ton"].values
    dates = forecast["shipment_date"]
    current_rate = float(rates[0])
    avg_rate = float(rates.mean())
    min_rate = float(rates.min())
    min_idx = int(rates.argmin())
    min_month = dates.iloc[min_idx].strftime("%B %Y")

    # Rate trajectory analysis
    first_half_avg = float(rates[:len(rates)//2].mean()) if len(rates) > 1 else current_rate
    second_half_avg = float(rates[len(rates)//2:].mean()) if len(rates) > 1 else current_rate
    trend_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

    # Volatility from confidence bounds
    if "rate_std" in forecast.columns:
        avg_uncertainty = float(forecast["rate_std"].mean())
    else:
        avg_uncertainty = float(np.std(rates))

    # Decision logic
    savings_pct = ((current_rate - min_rate) / current_rate * 100) if current_rate > 0 else 0

    if current_rate <= min_rate * 1.02:
        # Current rate is near the forecast minimum
        action = "BOOK NOW"
        confidence = "HIGH" if avg_uncertainty < 1.0 else "MEDIUM"
        rationale = (
            f"Current rate (${current_rate:.2f}/ton) is within 2% of the forecast minimum "
            f"(${min_rate:.2f}/ton in {min_month}). Rates are expected to {'rise' if trend_pct > 0 else 'remain stable'} "
            f"over the forecast horizon. Booking now locks in near-optimal pricing."
        )
    elif trend_pct > 5:
        # Rising market — book sooner
        action = "BOOK NOW"
        confidence = "MEDIUM" if avg_uncertainty < 2.0 else "LOW"
        rationale = (
            f"Rates are forecast to rise {trend_pct:.1f}% over the next {forecast_months} months. "
            f"Current rate ${current_rate:.2f}/ton is below the forecast average of ${avg_rate:.2f}/ton. "
            f"Delaying will likely increase costs."
        )
    elif savings_pct > 8:
        # Significant savings possible by waiting
        action = "WAIT"
        confidence = "MEDIUM" if avg_uncertainty < 2.0 else "LOW"
        rationale = (
            f"Forecast shows a rate trough of ${min_rate:.2f}/ton in {min_month}, "
            f"{savings_pct:.1f}% below current rate of ${current_rate:.2f}/ton. "
            f"Waiting could yield significant savings, but monitor volatility closely."
        )
    else:
        action = "HEDGE"
        confidence = "MEDIUM"
        rationale = (
            f"Market outlook is mixed. Current rate ${current_rate:.2f}/ton vs. "
            f"forecast average ${avg_rate:.2f}/ton. Consider splitting bookings across "
            f"multiple entry points to average out rate risk."
        )

    return MarketEntrySignal(
        action=action,
        confidence=confidence,
        current_rate=current_rate,
        forecast_avg=avg_rate,
        forecast_min=min_rate,
        forecast_min_month=min_month,
        potential_savings_pct=round(savings_pct, 1),
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Contract comparison (spot vs. term)
# ---------------------------------------------------------------------------
def compare_contract_strategies(
    model,
    origin_country: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    voyages_per_year: int = 6,
    feature_columns: list[str] | None = None,
) -> ContractComparison:
    """Compare spot, short-term, mid-term, and long-term contract costs."""
    # Forecast 12 months for full comparison
    forecast = forecast_rates(
        model, origin_country, destination_port, vessel_type,
        cargo_tonnes, months=12, feature_columns=feature_columns,
    )
    rates = forecast["rate_usd_per_ton"].values

    # Spot: each voyage at the prevailing rate
    # Simulate booking each voyage at the monthly rate
    spot_indices = np.linspace(0, len(rates) - 1, voyages_per_year, dtype=int)
    spot_rates = rates[spot_indices]
    spot_avg = float(spot_rates.mean())
    spot_total = spot_avg * cargo_tonnes * voyages_per_year

    # Short-term (1-3 months): 3-5% discount on average of first 3 months
    short_window = rates[:3] if len(rates) >= 3 else rates
    short_base = float(short_window.mean())
    short_discount = 0.04  # 4% term discount
    short_avg = short_base * (1 - short_discount)
    short_total = short_avg * cargo_tonnes * voyages_per_year

    # Mid-term (3-6 months): 6-10% discount
    mid_window = rates[:6] if len(rates) >= 6 else rates
    mid_base = float(mid_window.mean())
    mid_discount = 0.08  # 8% term discount
    mid_avg = mid_base * (1 - mid_discount)
    mid_total = mid_avg * cargo_tonnes * voyages_per_year

    # Long-term (6-12 months): 10-15% discount
    long_base = float(rates.mean())
    long_discount = 0.12  # 12% term discount
    long_avg = long_base * (1 - long_discount)
    long_total = long_avg * cargo_tonnes * voyages_per_year

    # Determine best strategy
    costs = {
        "Spot (individual bookings)": spot_total,
        "Short-term contract (1-3 months)": short_total,
        "Mid-term contract (3-6 months)": mid_total,
        "Long-term contract (6-12 months)": long_total,
    }
    best_strategy = min(costs, key=costs.get)
    best_cost = costs[best_strategy]
    savings_vs_spot = spot_total - best_cost

    return ContractComparison(
        spot_total_cost=round(spot_total, 0),
        spot_avg_rate=round(spot_avg, 2),
        spot_voyages=voyages_per_year,
        short_term_total_cost=round(short_total, 0),
        short_term_avg_rate=round(short_avg, 2),
        short_term_discount_pct=round(short_discount * 100, 1),
        mid_term_total_cost=round(mid_total, 0),
        mid_term_avg_rate=round(mid_avg, 2),
        mid_term_discount_pct=round(mid_discount * 100, 1),
        long_term_total_cost=round(long_total, 0),
        long_term_avg_rate=round(long_avg, 2),
        long_term_discount_pct=round(long_discount * 100, 1),
        recommended_strategy=best_strategy,
        savings_vs_spot=round(savings_vs_spot, 0),
    )


# ---------------------------------------------------------------------------
# Idle scenario management
# ---------------------------------------------------------------------------
def analyze_idle_scenarios(
    model,
    origin_country: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    feature_columns: list[str] | None = None,
) -> IdleScenario:
    """Identify potential idle periods and suggest mitigation strategies."""
    # Get vessel info
    vessel = next((v for v in VESSEL_CATALOG if v["vessel_type"] == vessel_type), None)
    if vessel is None:
        return IdleScenario()

    # Forecast demand patterns
    forecast = forecast_rates(
        model, origin_country, destination_port, vessel_type,
        cargo_tonnes, months=12, feature_columns=feature_columns,
    )
    rates = forecast["rate_usd_per_ton"].values
    dates = forecast["shipment_date"]

    # Identify low-demand months (below-average rate = lower demand)
    avg_rate = float(rates.mean())
    low_threshold = avg_rate * 0.95
    low_months = []
    for i, (rate, date) in enumerate(zip(rates, dates)):
        if rate < low_threshold:
            low_months.append(date.strftime("%B %Y"))

    # Estimate idle days based on monsoon and low demand
    idle_days = 0.0
    for date in dates:
        if date.month in (7, 8):  # peak monsoon
            idle_days += 5
        elif date.month in (6, 9):  # monsoon shoulder
            idle_days += 2

    idle_cost = idle_days * vessel["daily_cost_usd"]

    # Repositioning suggestions
    repo_suggestions = []
    if destination_port in ("Gopalpur", "Sagar-Sandheads"):
        repo_suggestions.append(
            f"During monsoon (Jun-Sep), reposition from {destination_port} to Gangavaram or Dhamra "
            f"for continued operations with deep-draft capability."
        )
    repo_suggestions.append(
        "Consider triangulation routes: after discharging at Indian East Coast, "
        "load iron ore or steel products for backhaul to East Asia (China, Japan, South Korea)."
    )

    # Backhaul opportunities
    backhaul = [
        "India → China: Iron ore exports from Paradip/Vizag to Chinese steel mills",
        "India → Japan: Steel product exports from Vizag to Japanese ports",
        "India → SE Asia: Rice/grain exports from Haldia to SE Asian markets",
    ]

    return IdleScenario(
        low_demand_months=low_months,
        estimated_idle_days=idle_days,
        idle_cost_usd=round(idle_cost, 0),
        repositioning_suggestions=repo_suggestions,
        backhaul_opportunities=backhaul,
    )


# ---------------------------------------------------------------------------
# What-if scenario simulator
# ---------------------------------------------------------------------------
def simulate_rate_scenario(
    model,
    origin_country: str,
    destination_port: str,
    vessel_type: str,
    cargo_tonnes: float,
    rate_change_pct: float,
    feature_columns: list[str] | None = None,
) -> dict:
    """Simulate the impact of a rate change (e.g., +10%, -15%) on total costs."""
    forecast = forecast_rates(
        model, origin_country, destination_port, vessel_type,
        cargo_tonnes, months=6, feature_columns=feature_columns,
    )

    base_rates = forecast["rate_usd_per_ton"].values
    base_total = float(base_rates.mean()) * cargo_tonnes
    adjusted_rates = base_rates * (1 + rate_change_pct / 100)
    adjusted_total = float(adjusted_rates.mean()) * cargo_tonnes

    return {
        "scenario": f"{'+'if rate_change_pct > 0 else ''}{rate_change_pct}% rate change",
        "base_avg_rate": round(float(base_rates.mean()), 2),
        "adjusted_avg_rate": round(float(adjusted_rates.mean()), 2),
        "base_total_cost": round(base_total, 0),
        "adjusted_total_cost": round(adjusted_total, 0),
        "cost_impact": round(adjusted_total - base_total, 0),
        "cost_impact_pct": round(rate_change_pct, 1),
    }
