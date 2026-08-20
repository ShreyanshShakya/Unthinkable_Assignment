from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from app.db.session import get_db
from app.models import RateCard, RateCardRule, CODSurcharge, Zone, OrderType, ZoneType
from app.schemas.zone import (
    RateCardCreate, RateCardUpdate, RateCardResponse,
    RateCardRuleCreate, RateCardRuleUpdate, RateCardRuleResponse,
    CODSurchargeCreate, CODSurchargeUpdate, CODSurchargeResponse
)
from app.api.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/rate-cards", response_model=RateCardResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_card(rate_card_data: RateCardCreate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    if rate_card_data.order_type not in [ot.value for ot in OrderType]:
        raise HTTPException(status_code=400, detail="Invalid order type")
    if rate_card_data.zone_type not in [zt.value for zt in ZoneType]:
        raise HTTPException(status_code=400, detail="Invalid zone type")
    
    result = await db.execute(
        select(RateCard).where(
            RateCard.name == rate_card_data.name,
            RateCard.order_type == rate_card_data.order_type,
            RateCard.zone_type == rate_card_data.zone_type
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Rate card with this name, order type, and zone type already exists")
    
    rate_card = RateCard(**rate_card_data.model_dump())
    db.add(rate_card)
    await db.commit()
    await db.refresh(rate_card)
    return rate_card


@router.get("/rate-cards", response_model=List[RateCardResponse])
async def list_rate_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    order_type: Optional[str] = None,
    zone_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin)
):
    query = select(RateCard)
    if order_type:
        query = query.where(RateCard.order_type == order_type)
    if zone_type:
        query = query.where(RateCard.zone_type == zone_type)
    if is_active is not None:
        query = query.where(RateCard.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(RateCard.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/rate-cards/{rate_card_id}", response_model=RateCardResponse)
async def get_rate_card(rate_card_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    rate_card = result.scalar_one_or_none()
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    return rate_card


@router.put("/rate-cards/{rate_card_id}", response_model=RateCardResponse)
async def update_rate_card(rate_card_id: UUID, rate_card_data: RateCardUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    rate_card = result.scalar_one_or_none()
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    for field, value in rate_card_data.model_dump(exclude_unset=True).items():
        setattr(rate_card, field, value)
    
    await db.commit()
    await db.refresh(rate_card)
    return rate_card


@router.delete("/rate-cards/{rate_card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_card(rate_card_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    rate_card = result.scalar_one_or_none()
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    rate_card.is_active = False
    await db.commit()


@router.post("/rate-cards/{rate_card_id}/rules", response_model=RateCardRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_card_rule(rate_card_id: UUID, rule_data: RateCardRuleCreate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    if rule_data.rate_card_id != rate_card_id:
        raise HTTPException(status_code=400, detail="Rate card ID mismatch")
    
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    rate_card = result.scalar_one_or_none()
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    result = await db.execute(select(Zone).where(Zone.id == rule_data.pickup_zone_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Pickup zone not found")
    
    result = await db.execute(select(Zone).where(Zone.id == rule_data.drop_zone_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Drop zone not found")
    
    if rule_data.max_weight_kg is not None and rule_data.max_weight_kg <= rule_data.min_weight_kg:
        raise HTTPException(status_code=400, detail="Max weight must be greater than min weight")
    
    rule = RateCardRule(**rule_data.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/rate-cards/{rate_card_id}/rules", response_model=List[RateCardRuleResponse])
async def list_rate_card_rules(
    rate_card_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin)
):
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    query = select(RateCardRule).where(RateCardRule.rate_card_id == rate_card_id)
    query = query.offset(skip).limit(limit).order_by(RateCardRule.min_weight_kg)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/rate-rules/{rule_id}", response_model=RateCardRuleResponse)
async def update_rate_card_rule(rule_id: UUID, rule_data: RateCardRuleUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(RateCardRule).where(RateCardRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rate rule not found")
    
    min_weight = rule_data.min_weight_kg if rule_data.min_weight_kg is not None else rule.min_weight_kg
    max_weight = rule_data.max_weight_kg if rule_data.max_weight_kg is not None else rule.max_weight_kg
    
    if max_weight is not None and max_weight <= min_weight:
        raise HTTPException(status_code=400, detail="Max weight must be greater than min weight")
    
    for field, value in rule_data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rate-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_card_rule(rule_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(RateCardRule).where(RateCardRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rate rule not found")
    
    await db.delete(rule)
    await db.commit()


@router.post("/rate-cards/{rate_card_id}/cod-surcharges", response_model=CODSurchargeResponse, status_code=status.HTTP_201_CREATED)
async def create_cod_surcharge(rate_card_id: UUID, surcharge_data: CODSurchargeCreate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    if surcharge_data.rate_card_id != rate_card_id:
        raise HTTPException(status_code=400, detail="Rate card ID mismatch")
    
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    rate_card = result.scalar_one_or_none()
    if not rate_card:
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    if surcharge_data.max_order_value is not None and surcharge_data.max_order_value <= surcharge_data.min_order_value:
        raise HTTPException(status_code=400, detail="Max order value must be greater than min order value")
    
    if surcharge_data.max_surcharge is not None and surcharge_data.max_surcharge < surcharge_data.min_surcharge:
        raise HTTPException(status_code=400, detail="Max surcharge must be greater than or equal to min surcharge")
    
    surcharge = CODSurcharge(**surcharge_data.model_dump())
    db.add(surcharge)
    await db.commit()
    await db.refresh(surcharge)
    return surcharge


@router.get("/rate-cards/{rate_card_id}/cod-surcharges", response_model=List[CODSurchargeResponse])
async def list_cod_surcharges(
    rate_card_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin)
):
    result = await db.execute(select(RateCard).where(RateCard.id == rate_card_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Rate card not found")
    
    query = select(CODSurcharge).where(CODSurcharge.rate_card_id == rate_card_id)
    if is_active is not None:
        query = query.where(CODSurcharge.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(CODSurcharge.min_order_value)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/cod-surcharges/{surcharge_id}", response_model=CODSurchargeResponse)
async def update_cod_surcharge(surcharge_id: UUID, surcharge_data: CODSurchargeUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(CODSurcharge).where(CODSurcharge.id == surcharge_id))
    surcharge = result.scalar_one_or_none()
    if not surcharge:
        raise HTTPException(status_code=404, detail="COD surcharge not found")
    
    min_order = surcharge_data.min_order_value if surcharge_data.min_order_value is not None else surcharge.min_order_value
    max_order = surcharge_data.max_order_value if surcharge_data.max_order_value is not None else surcharge.max_order_value
    
    if max_order is not None and max_order <= min_order:
        raise HTTPException(status_code=400, detail="Max order value must be greater than min order value")
    
    min_surcharge = surcharge_data.min_surcharge if surcharge_data.min_surcharge is not None else surcharge.min_surcharge
    max_surcharge = surcharge_data.max_surcharge if surcharge_data.max_surcharge is not None else surcharge.max_surcharge
    
    if max_surcharge is not None and max_surcharge < min_surcharge:
        raise HTTPException(status_code=400, detail="Max surcharge must be greater than or equal to min surcharge")
    
    for field, value in surcharge_data.model_dump(exclude_unset=True).items():
        setattr(surcharge, field, value)
    
    await db.commit()
    await db.refresh(surcharge)
    return surcharge


@router.delete("/cod-surcharges/{surcharge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cod_surcharge(surcharge_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(CODSurcharge).where(CODSurcharge.id == surcharge_id))
    surcharge = result.scalar_one_or_none()
    if not surcharge:
        raise HTTPException(status_code=404, detail="COD surcharge not found")
    
    await db.delete(surcharge)
    await db.commit()