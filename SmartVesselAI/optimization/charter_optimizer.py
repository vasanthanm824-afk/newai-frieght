import os
import sys

SMARTVESSEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SMARTVESSEL_DIR not in sys.path:
    sys.path.insert(0, SMARTVESSEL_DIR)

try:
    from backend.database import SessionLocal
    from backend.models.db_models import Vessel, Port, FreightRate
    from ml.predict import FreightPredictor
except ModuleNotFoundError:
    from SmartVesselAI.backend.database import SessionLocal
    from SmartVesselAI.backend.models.db_models import Vessel, Port, FreightRate
    from SmartVesselAI.ml.predict import FreightPredictor

class CharterOptimizer:
    def __init__(self):
        self.predictor = FreightPredictor()

    def check_port_compatibility(self, vessel: Vessel, port: Port, cargo_tonnes: float):
        """
        Validates 4 main constraints:
        1. Vessel Draft <= Port Max Draft
        2. Vessel LOA <= Port Max LOA
        3. Vessel Beam <= Port Max Beam
        4. Cargo Quantity <= Vessel Capacity
        """
        draft_ok = vessel.draft <= port.max_draft
        loa_ok = vessel.loa <= port.max_loa
        beam_ok = vessel.beam <= port.max_beam
        capacity_ok = cargo_tonnes <= vessel.capacity

        is_compatible = draft_ok and loa_ok and beam_ok and capacity_ok
        reasons = []

        if not draft_ok:
            reasons.append(f"Draft ({vessel.draft}m) exceeds port max draft ({port.max_draft}m).")
        if not loa_ok:
            reasons.append(f"Length Overall ({vessel.loa}m) exceeds port max LOA ({port.max_loa}m).")
        if not beam_ok:
            reasons.append(f"Beam ({vessel.beam}m) exceeds port max beam ({port.max_beam}m).")
        if not capacity_ok:
            reasons.append(f"Cargo quantity ({cargo_tonnes:,.0f} T) exceeds vessel capacity ({vessel.capacity:,.0f} T).")

        if is_compatible:
            reasons.append("Vessel passes all port dimension and capacity checks.")

        return {
            "is_compatible": is_compatible,
            "draft_check": {"vessel": vessel.draft, "port_max": port.max_draft, "pass": draft_ok},
            "loa_check": {"vessel": vessel.loa, "port_max": port.max_loa, "pass": loa_ok},
            "beam_check": {"vessel": vessel.beam, "port_max": port.max_beam, "pass": beam_ok},
            "capacity_check": {"vessel_capacity": vessel.capacity, "cargo": cargo_tonnes, "pass": capacity_ok},
            "reasons": reasons
        }

    def optimize(self, origin: str, destination: str, cargo_tonnes: float, commodity: str = "Coal"):
        db = SessionLocal()
        try:
            # 1. Fetch destination port info
            port = db.query(Port).filter(Port.port_name == destination).first()
            if not port:
                port = db.query(Port).first()

            # 2. Get ML rate predictions
            pred = self.predictor.predict(origin, destination, "Panamax")
            rate_per_tonne = pred["current_rate"]
            trend = pred["trend"]

            # 3. Get all available vessels
            vessels = db.query(Vessel).all()
            options = []

            for v in vessels:
                compat = self.check_port_compatibility(v, port, cargo_tonnes)
                is_compat = compat["is_compatible"]

                # Voyage calculations (assume 3500 nautical miles average voyage)
                voyage_distance_nm = 3500.0
                speed_knots = v.speed or 13.0
                voyage_hours = voyage_distance_nm / speed_knots
                sailing_days = voyage_hours / 24.0

                fuel_price_mt = 620.0 # VLSFO $/MT
                daily_fuel_consumption = v.fuel_consumption or 28.0

                # Costs in Lakhs (₹ INR) for user presentation
                # 1 USD = 83 INR, 1 Lakh = 100,000 INR
                usd_to_inr = 83.0
                
                freight_cost_usd = cargo_tonnes * (rate_per_tonne / 10.0) # Normalized benchmark rate
                fuel_cost_usd = sailing_days * daily_fuel_consumption * fuel_price_mt
                port_cost_usd = 15000.0 + (cargo_tonnes * 0.15)
                waiting_days = port.avg_waiting_days if port else 2.0
                waiting_cost_usd = waiting_days * (v.daily_charter_rate or 14000.0)
                idle_cost_usd = 1.0 * (v.daily_charter_rate or 14000.0)
                
                # Penalty if incompatible
                risk_penalty_usd = 0.0 if is_compat else 250000.0

                total_cost_usd = freight_cost_usd + fuel_cost_usd + port_cost_usd + waiting_cost_usd + idle_cost_usd + risk_penalty_usd
                
                # Convert to Lakhs INR (1 Lakh = 100,000 INR)
                freight_lakhs = round((freight_cost_usd * usd_to_inr) / 100000.0, 2)
                fuel_lakhs = round((fuel_cost_usd * usd_to_inr) / 100000.0, 2)
                port_lakhs = round((port_cost_usd * usd_to_inr) / 100000.0, 2)
                waiting_lakhs = round((waiting_cost_usd * usd_to_inr) / 100000.0, 2)
                idle_lakhs = round((idle_cost_usd * usd_to_inr) / 100000.0, 2)
                risk_lakhs = round((risk_penalty_usd * usd_to_inr) / 100000.0, 2)
                total_lakhs = round((total_cost_usd * usd_to_inr) / 100000.0, 2)

                # Score evaluation (lower total cost & compatible = better score)
                score = (1.0 / (total_lakhs + 1.0)) * (100.0 if is_compat else 1.0) * 1000.0

                risk_level = "LOW" if (is_compat and waiting_days <= 2.0) else ("MEDIUM" if is_compat else "HIGH")
                
                # Recommendation Action Badge
                if not is_compat:
                    action = "INCOMPATIBLE"
                elif trend == "DECREASING":
                    action = "WAIT (Rate Dropping)"
                else:
                    action = "CHART NOW"

                options.append({
                    "vessel_name": v.vessel_name,
                    "vessel_type": v.vessel_type,
                    "is_compatible": is_compat,
                    "freight_cost": freight_lakhs,
                    "fuel_cost": fuel_lakhs,
                    "port_cost": port_lakhs,
                    "waiting_cost": waiting_lakhs,
                    "idle_cost": idle_lakhs,
                    "risk_penalty": risk_lakhs,
                    "total_cost": total_lakhs,
                    "freight_cost_usd": round(freight_cost_usd, 2),
                    "fuel_cost_usd": round(fuel_cost_usd, 2),
                    "port_cost_usd": round(port_cost_usd, 2),
                    "waiting_cost_usd": round(waiting_cost_usd, 2),
                    "idle_cost_usd": round(idle_cost_usd, 2),
                    "risk_penalty_usd": round(risk_penalty_usd, 2),
                    "total_cost_usd": round(total_cost_usd, 2),
                    "score": round(score, 2),
                    "risk_level": risk_level,
                    "recommendation_action": action,
                    "compat_details": compat
                })

            # Sort options by score descending (best option first)
            options.sort(key=lambda x: x["score"], reverse=True)

            best_option = options[0] if options else None
            
            explanations = []
            if best_option:
                if best_option["is_compatible"]:
                    explanations.append(f"Suitable cargo capacity for {cargo_tonnes:,.0f} T.")
                    explanations.append(f"Port compatible with {destination} (Draft & LOA within limits).")
                    explanations.append("Lowest estimated total voyage cost.")
                    explanations.append(f"Acceptable waiting risk ({best_option['risk_level']} Risk).")
                else:
                    explanations.append("No fully compatible vessel found for requested cargo & port dimensions.")

            rec_action = "CHARTER NOW" if (best_option and best_option["recommendation_action"] == "CHART NOW") else ("WAIT" if (trend == "DECREASING") else "RE-EVALUATE")

            return {
                "cargo_summary": {
                    "origin": origin,
                    "destination": destination,
                    "commodity": commodity,
                    "cargo_tonnes": cargo_tonnes
                },
                "recommended_vessel": best_option["vessel_name"] if best_option else "N/A",
                "recommended_action": rec_action,
                "estimated_total_cost": best_option["total_cost"] if best_option else 0.0,
                "estimated_total_cost_usd": best_option["total_cost_usd"] if best_option else 0.0,
                "explanation": explanations,
                "all_options": options
            }

        finally:
            db.close()

if __name__ == "__main__":
    optimizer = CharterOptimizer()
    res = optimizer.optimize("Australia", "Paradip", 80000.0, "Coal")
    print("Optimization Result:")
    print(f"Recommended Vessel: {res['recommended_vessel']}")
    print(f"Recommended Action: {res['recommended_action']}")
    print(f"Estimated Total Cost: INR {res['estimated_total_cost']} Lakhs")
    for exp in res['explanation']:
        print(f"  - {exp}")
