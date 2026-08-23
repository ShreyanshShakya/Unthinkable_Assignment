from fastapi import APIRouter, Depends

from app.api.deps import require_customer
from app.models import User
from app.schemas.pricing import PricingRequest, PricingResponse, QuoteRequest, QuoteResponse
from app.services.pricing import PricingEngine, get_pricing_engine

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.post("/calculate", response_model=PricingResponse)
async def calculate_price(
    request: PricingRequest,
    pricing_engine: PricingEngine = Depends(get_pricing_engine),
    current_user: User = Depends(require_customer)
):
    """Calculate price for given parameters (requires zone IDs)"""
    result = await pricing_engine.calculate_price(request)

    if not result["success"]:
        return PricingResponse(success=False, error=result["error"])

    breakdown = result["breakdown"]
    return PricingResponse(
        success=True,
        breakdown={
            "volumetric_weight_kg": breakdown["volumetric_weight_kg"],
            "billable_weight_kg": breakdown["billable_weight_kg"],
            "zone_type": breakdown["zone_type"],
            "rate_card_id": breakdown["rate_card_id"],
            "base_charge": breakdown["base_charge"],
            "cod_surcharge": breakdown["cod_surcharge"],
            "total_charge": breakdown["total_charge"],
            "applied_rule": breakdown["applied_rule"],
            "applied_cod_surcharge": breakdown["applied_cod_surcharge"]
        }
    )


@router.post("/quote", response_model=QuoteResponse)
async def get_quote(
    request: QuoteRequest,
    pricing_engine: PricingEngine = Depends(get_pricing_engine),
    current_user: User = Depends(require_customer)
):
    """Get price quote with automatic zone detection from pincodes"""
    result = await pricing_engine.calculate_quote(request)

    if not result["success"]:
        return QuoteResponse(success=False, error=result["error"])

    breakdown = result["breakdown"]
    return QuoteResponse(
        success=True,
        pricing={
            "volumetric_weight_kg": breakdown["volumetric_weight_kg"],
            "billable_weight_kg": breakdown["billable_weight_kg"],
            "zone_type": breakdown["zone_type"],
            "rate_card_id": breakdown["rate_card_id"],
            "base_charge": breakdown["base_charge"],
            "cod_surcharge": breakdown["cod_surcharge"],
            "total_charge": breakdown["total_charge"],
            "applied_rule": breakdown["applied_rule"],
            "applied_cod_surcharge": breakdown["applied_cod_surcharge"]
        },
        pickup_zone=result.get("pickup_zone"),
        drop_zone=result.get("drop_zone")
    )


@router.get("/rate-cards/active")
async def list_active_rate_cards(
    pricing_engine: PricingEngine = Depends(get_pricing_engine),
    current_user: User = Depends(require_customer)
):
    """List all active rate cards for reference"""
    from sqlalchemy import select

    from app.models import RateCard

    result = await pricing_engine.db.execute(
        select(RateCard).where(RateCard.is_active == True)
    )
    rate_cards = result.scalars().all()

    return [
        {
            "id": str(rc.id),
            "name": rc.name,
            "order_type": rc.order_type.value,
            "zone_type": rc.zone_type.value,
            "effective_from": rc.effective_from.isoformat(),
            "effective_to": rc.effective_to.isoformat() if rc.effective_to else None
        }
        for rc in rate_cards
    ]
