from typing import Optional, Tuple
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import (
    RateCard, RateCardRule, CODSurcharge, Zone, OrderType, 
    PaymentType, ZoneType
)
from app.services.zone_detection import ZoneDetectionService
from app.db.session import get_db


class PricingEngine:
    """Core pricing calculation engine"""
    
    VOLUMETRIC_DIVISOR = 5000  # cm³ per kg
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.zone_service = ZoneDetectionService(db)
    
    def calculate_volumetric_weight(self, length_cm: float, breadth_cm: float, height_cm: float) -> float:
        """Calculate volumetric weight: L × B × H / 5000"""
        volume = length_cm * breadth_cm * height_cm
        return round(volume / self.VOLUMETRIC_DIVISOR, 3)
    
    def calculate_billable_weight(self, actual_weight: float, volumetric_weight: float) -> float:
        """Billable weight = max(actual weight, volumetric weight)"""
        return round(max(actual_weight, volumetric_weight), 3)
    
    async def get_rate_card(
        self, 
        order_type: OrderType, 
        zone_type: ZoneType
    ) -> Optional[RateCard]:
        """Get active rate card for order type and zone type"""
        result = await self.db.execute(
            select(RateCard)
            .where(RateCard.order_type == order_type)
            .where(RateCard.zone_type == zone_type)
            .where(RateCard.is_active == True)
            .order_by(RateCard.effective_from.desc())
        )
        return result.scalars().first()
    
    async def find_applicable_rule(
        self, 
        rate_card_id: UUID, 
        pickup_zone_id: UUID, 
        drop_zone_id: UUID, 
        billable_weight: float
    ) -> Optional[RateCardRule]:
        """Find the rate card rule that matches the shipment"""
        result = await self.db.execute(
            select(RateCardRule)
            .where(RateCardRule.rate_card_id == rate_card_id)
            .where(RateCardRule.pickup_zone_id == pickup_zone_id)
            .where(RateCardRule.drop_zone_id == drop_zone_id)
            .where(RateCardRule.min_weight_kg <= billable_weight)
            .where(
                (RateCardRule.max_weight_kg.is_(None)) | 
                (RateCardRule.max_weight_kg >= billable_weight)
            )
            .order_by(RateCardRule.min_weight_kg.desc())
        )
        return result.scalars().first()
    
    def calculate_base_charge(self, rule: RateCardRule, billable_weight: float) -> float:
        """Calculate base charge from rate rule"""
        # Base charge + (billable_weight - min_weight) * per_kg_charge
        additional_weight = max(0, billable_weight - float(rule.min_weight_kg))
        base_charge = float(rule.base_charge) + (additional_weight * float(rule.per_kg_charge))
        return round(base_charge, 2)
    
    async def get_cod_surcharge(self, rate_card_id: UUID, order_value: float) -> Tuple[float, Optional[CODSurcharge]]:
        """Get applicable COD surcharge for order value"""
        result = await self.db.execute(
            select(CODSurcharge)
            .where(CODSurcharge.rate_card_id == rate_card_id)
            .where(CODSurcharge.is_active == True)
            .where(CODSurcharge.min_order_value <= order_value)
            .where(
                (CODSurcharge.max_order_value.is_(None)) | 
                (CODSurcharge.max_order_value >= order_value)
            )
            .order_by(CODSurcharge.min_order_value.desc())
        )
        surcharge = result.scalars().first()
        
        if not surcharge:
            return 0.0, None
        
        surcharge_amount = (order_value * float(surcharge.surcharge_percentage)) / 100
        surcharge_amount = max(surcharge_amount, float(surcharge.min_surcharge))
        
        if surcharge.max_surcharge is not None:
            surcharge_amount = min(surcharge_amount, float(surcharge.max_surcharge))
        
        return round(surcharge_amount, 2), surcharge
    
    async def calculate_price(self, request) -> dict:
        """Main pricing calculation"""
        try:
            # 1. Calculate volumetric weight
            volumetric_weight = self.calculate_volumetric_weight(
                request.length_cm, request.breadth_cm, request.height_cm
            )
            
            # 2. Calculate billable weight
            billable_weight = self.calculate_billable_weight(
                request.actual_weight_kg, volumetric_weight
            )
            
            # 3. Determine zone type
            zone_type = ZoneType.INTRA_ZONE if request.pickup_zone_id == request.drop_zone_id else ZoneType.INTER_ZONE
            
            # 4. Get rate card
            rate_card = await self.get_rate_card(request.order_type, zone_type)
            if not rate_card:
                return {
                    "success": False,
                    "error": f"No rate card found for {request.order_type.value} {zone_type.value}"
                }
            
            # 5. Find applicable rule
            rule = await self.find_applicable_rule(
                rate_card.id, request.pickup_zone_id, request.drop_zone_id, billable_weight
            )
            if not rule:
                return {
                    "success": False,
                    "error": f"No rate rule found for weight {billable_weight}kg between zones"
                }
            
            # 6. Calculate base charge
            base_charge = self.calculate_base_charge(rule, billable_weight)
            
            # 7. Calculate COD surcharge if applicable
            cod_surcharge = 0.0
            applied_cod = None
            if request.payment_type == PaymentType.COD:
                cod_surcharge, applied_cod = await self.get_cod_surcharge(rate_card.id, request.order_value)
            
            # 8. Total charge
            total_charge = round(base_charge + cod_surcharge, 2)
            
            return {
                "success": True,
                "breakdown": {
                    "volumetric_weight_kg": volumetric_weight,
                    "billable_weight_kg": billable_weight,
                    "zone_type": zone_type,
                    "rate_card_id": rate_card.id,
                    "base_charge": base_charge,
                    "cod_surcharge": cod_surcharge,
                    "total_charge": total_charge,
                    "applied_rule": f"{rule.min_weight_kg}kg - {rule.max_weight_kg or '∞'}kg: ₹{rule.base_charge} + ₹{rule.per_kg_charge}/kg",
                    "applied_cod_surcharge": f"{applied_cod.surcharge_percentage}% (min ₹{applied_cod.min_surcharge}, max ₹{applied_cod.max_surcharge or '∞'})" if applied_cod else None
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def calculate_quote(self, request) -> dict:
        """Calculate quote with zone detection"""
        try:
            # Detect zones
            pickup_zone, drop_zone = await self.zone_service.get_pickup_drop_zones(
                pickup_pincode=request.pickup_pincode,
                pickup_city=request.pickup_city,
                pickup_state=request.pickup_state,
                drop_pincode=request.drop_pincode,
                drop_city=request.drop_city,
                drop_state=request.drop_state
            )
            
            if not pickup_zone:
                return {"success": False, "error": f"Pickup zone not found for pincode {request.pickup_pincode}"}
            if not drop_zone:
                return {"success": False, "error": f"Drop zone not found for pincode {request.drop_pincode}"}
            
            # Create pricing request with detected zones
            from app.schemas.pricing import PricingRequest
            pricing_request = PricingRequest(
                length_cm=request.length_cm,
                breadth_cm=request.breadth_cm,
                height_cm=request.height_cm,
                actual_weight_kg=request.actual_weight_kg,
                order_type=request.order_type,
                payment_type=request.payment_type,
                pickup_zone_id=pickup_zone.id,
                drop_zone_id=drop_zone.id,
                order_value=request.order_value
            )
            
            result = await self.calculate_price(pricing_request)
            
            if result["success"]:
                result["pickup_zone"] = {"id": str(pickup_zone.id), "name": pickup_zone.name, "code": pickup_zone.code}
                result["drop_zone"] = {"id": str(drop_zone.id), "name": drop_zone.name, "code": drop_zone.code}
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}


async def get_pricing_engine(db: AsyncSession = Depends(get_db)) -> PricingEngine:
    from fastapi import Depends
    from app.db.session import get_db
    return PricingEngine(db)