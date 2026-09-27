"""Voyage router — cost breakdown and vessel comparison."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from ..core.voyage_calculator import compare_all_vessels, compute_voyage_cost

router = APIRouter()


class VoyageCostRequest(BaseModel):
    origin_country: str
    origin_port: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    destination_country: str = "India"


@router.post("/cost")
def get_voyage_cost(req: VoyageCostRequest):
    result = compute_voyage_cost(
        req.origin_country, req.origin_port, req.destination_port,
        req.vessel_type, req.cargo_tonnes, destination_country=req.destination_country,
    )
    if result is None:
        return {"error": "Could not compute voyage cost"}
    return {"voyage": asdict(result)}


class CompareRequest(BaseModel):
    origin_country: str
    origin_port: str
    destination_port: str
    cargo_tonnes: float
    destination_country: str = "India"


@router.post("/compare-all")
def compare_voyages(req: CompareRequest):
    results = compare_all_vessels(
        req.origin_country, req.origin_port, req.destination_port, req.cargo_tonnes,
    )
    return {"voyages": [asdict(v) for v in results]}


class BillingRequest(BaseModel):
    origin_country: str
    origin_port: str
    destination_port: str
    vessel_type: str
    cargo_tonnes: float
    spot_rate_per_ton: float = 25.0
    discount_pct: float = 0.0
    tax_pct: float = 5.0
    currency: str = "USD"
    custom_line_items: list[dict] | None = None


@router.post("/billing")
def calculate_billing(req: BillingRequest):
    result = compute_voyage_cost(
        req.origin_country, req.origin_port, req.destination_port,
        req.vessel_type, req.cargo_tonnes,
    )
    
    base_freight = req.spot_rate_per_ton * req.cargo_tonnes
    vessel_hire = result.vessel_hire_usd if result else 250000.0
    fuel_cost = result.fuel_cost_usd if result else 180000.0
    port_charges_load = result.port_charges_load_usd if result else 45000.0
    port_charges_discharge = result.port_charges_discharge_usd if result else 55000.0
    eco_levy = round(base_freight * 0.015, 2)
    idle_provision = 25000.0

    if req.custom_line_items and len(req.custom_line_items) > 0:
        line_items = req.custom_line_items
        subtotal = sum(float(li.get("amount_usd", 0)) for li in line_items)
    else:
        subtotal = base_freight + vessel_hire + fuel_cost + port_charges_load + port_charges_discharge + eco_levy + idle_provision
        line_items = [
            {"item": "Base Ocean Freight Charge", "details": f"{req.cargo_tonnes:,.0f} MT @ ${req.spot_rate_per_ton:.2f}/MT", "amount_usd": base_freight},
            {"item": "Vessel Time Charter Hire", "details": f"{result.sailing_days if result else 15} days sailing + laytime", "amount_usd": vessel_hire},
            {"item": "Bunker Fuel Consumption (VLSFO/MGO)", "details": "At current Baltic bunker rates", "amount_usd": fuel_cost},
            {"item": "Loading Port Charges & Berth Dues", "details": f"Port of {req.origin_port}, {req.origin_country}", "amount_usd": port_charges_load},
            {"item": "Discharge Port Charges & Handling", "details": f"Port of {req.destination_port}, India", "amount_usd": port_charges_discharge},
            {"item": "Maritime Carbon & Eco Compliance Levy", "details": "IMO 2026 / EU ETS Carbon Allowance (1.5%)", "amount_usd": eco_levy},
            {"item": "Port Idle & Congestion Provision", "details": "Estimated 2-3 days waiting buffer", "amount_usd": idle_provision},
        ]
    
    discount_amount = round(subtotal * (req.discount_pct / 100.0), 2)
    subtotal_after_discount = subtotal - discount_amount
    tax_amount = round(subtotal_after_discount * (req.tax_pct / 100.0), 2)
    grand_total_usd = subtotal_after_discount + tax_amount
    grand_total_inr = grand_total_usd * 83.5
    cost_per_ton_usd = round(grand_total_usd / req.cargo_tonnes, 2) if req.cargo_tonnes > 0 else 0
    
    inv_no = f"INV-2026-FRT-{abs(hash(req.origin_port + req.destination_port)) % 10000:04d}"

    formatted_items = ""
    for idx, li in enumerate(line_items, 1):
        formatted_items += f"  {idx}. {li['item']:<48}: $ {li['amount_usd']:>12,.2f}\n"
        formatted_items += f"     ({li['details']})\n"

    formatted_text_invoice = f"""========================================================================================
                      SMARTVESSEL AI - MARITIME CHARTER PRO-FORMA INVOICE
========================================================================================
Invoice Reference  : {inv_no}
Issue Date         : 02 Sep 2026
Payment Terms      : Net 30 Days / Pro-Forma Letter of Credit
Status             : PRO-FORMA INVOICE GENERATED
----------------------------------------------------------------------------------------
CHARTER & VOYAGE DETAILS:
  Loading Port     : {req.origin_port}, {req.origin_country}
  Discharge Port   : {req.destination_port}, India
  Vessel Category  : {req.vessel_type} Bulk Carrier
  Cargo Volume     : {req.cargo_tonnes:,.0f} MT
  Spot Freight Rate: ${req.spot_rate_per_ton:.2f} / MT
----------------------------------------------------------------------------------------
ITEMIZED COST BREAKDOWN (USD):
{formatted_items}----------------------------------------------------------------------------------------
FINANCIAL SUMMARY:
  Gross Subtotal                                     : $ {subtotal:>12,.2f}
  Contract Discount ({req.discount_pct:.1f}%)                           : -$ {discount_amount:>12,.2f}
  Subtotal After Discount                            : $ {subtotal_after_discount:>12,.2f}
  Statutory Customs & Port Dues ({req.tax_pct:.1f}%)               : +$ {tax_amount:>12,.2f}
  ------------------------------------------------------------------
  NET PAYABLE AMOUNT (USD)                           : $ {grand_total_usd:>12,.2f} USD
  NET PAYABLE AMOUNT (INR EQUIVALENT)                : ₹ {grand_total_inr:>12,.0f} INR
  NET UNIT FREIGHT COST                              : $ {cost_per_ton_usd:>12.2f} / MT
========================================================================================
REMITTANCE & PAYMENT INSTRUCTIONS:
  Bank Name        : Maritime International Commercial Bank
  SWIFT Code       : MARIINBBXXX
  Account Name     : SmartVessel AI Freight Operations Escrow
  Account Number   : 9874-2026-4410
  Reference        : {inv_no}
========================================================================================
"""

    return {
        "status": "success",
        "invoice_number": inv_no,
        "billing_summary": {
            "origin": f"{req.origin_port}, {req.origin_country}",
            "destination": f"{req.destination_port}, India",
            "vessel_type": req.vessel_type,
            "cargo_tonnes": req.cargo_tonnes,
            "line_items": line_items,
            "subtotal_usd": subtotal,
            "discount_pct": req.discount_pct,
            "discount_amount_usd": discount_amount,
            "tax_pct": req.tax_pct,
            "tax_amount_usd": tax_amount,
            "grand_total_usd": grand_total_usd,
            "grand_total_inr": grand_total_inr,
            "cost_per_ton_usd": cost_per_ton_usd,
            "payment_status": "PRO-FORMA INVOICE GENERATED",
            "formatted_text_invoice": formatted_text_invoice,
        }
    }


@router.post("/billing/text")
def get_billing_text_invoice(req: BillingRequest):
    res = calculate_billing(req)
    text = res["billing_summary"]["formatted_text_invoice"]
    from fastapi import Response
    return Response(content=text, media_type="text/plain")

