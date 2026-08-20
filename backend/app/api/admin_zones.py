from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.models import Zone, ZoneArea, RateCard, RateCardRule, CODSurcharge, OrderType, ZoneType
from app.schemas.zone import (
    ZoneCreate, ZoneUpdate, ZoneResponse,
    ZoneAreaCreate, ZoneAreaUpdate, ZoneAreaResponse,
    RateCardCreate, RateCardUpdate, RateCardResponse,
    RateCardRuleCreate, RateCardRuleUpdate, RateCardRuleResponse,
    CODSurchargeCreate, CODSurchargeUpdate, CODSurchargeResponse
)
from app.api.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/zones", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_zone(zone_data: ZoneCreate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(Zone).where(Zone.code == zone_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Zone code already exists")
    
    result = await db.execute(select(Zone).where(Zone.name == zone_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Zone name already exists")
    
    zone = Zone(**zone_data.model_dump())
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.get("/zones", response_model=List[ZoneResponse])
async def list_zones(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin)
):
    query = select(Zone)
    if is_active is not None:
        query = query.where(Zone.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(Zone.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(zone_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(zone_id: UUID, zone_data: ZoneUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    if zone_data.code and zone_data.code != zone.code:
        result = await db.execute(select(Zone).where(Zone.code == zone_data.code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Zone code already exists")
    
    if zone_data.name and zone_data.name != zone.name:
        result = await db.execute(select(Zone).where(Zone.name == zone_data.name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Zone name already exists")
    
    for field, value in zone_data.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    
    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(zone_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    zone.is_active = False
    await db.commit()


@router.post("/zones/{zone_id}/areas", response_model=ZoneAreaResponse, status_code=status.HTTP_201_CREATED)
async def add_zone_area(zone_id: UUID, area_data: ZoneAreaCreate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    if area_data.zone_id != zone_id:
        raise HTTPException(status_code=400, detail="Zone ID mismatch")
    
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    result = await db.execute(
        select(ZoneArea).where(ZoneArea.zone_id == zone_id, ZoneArea.pincode == area_data.pincode)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Pincode already exists in this zone")
    
    area = ZoneArea(**area_data.model_dump())
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return area


@router.get("/zones/{zone_id}/areas", response_model=List[ZoneAreaResponse])
async def list_zone_areas(
    zone_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin)
):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Zone not found")
    
    query = select(ZoneArea).where(ZoneArea.zone_id == zone_id)
    if is_active is not None:
        query = query.where(ZoneArea.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(ZoneArea.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/areas/{area_id}", response_model=ZoneAreaResponse)
async def update_zone_area(area_id: UUID, area_data: ZoneAreaUpdate, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(ZoneArea).where(ZoneArea.id == area_id))
    area = result.scalar_one_or_none()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    if area_data.pincode and area_data.pincode != area.pincode:
        result = await db.execute(
            select(ZoneArea).where(ZoneArea.zone_id == area.zone_id, ZoneArea.pincode == area_data.pincode)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Pincode already exists in this zone")
    
    for field, value in area_data.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    
    await db.commit()
    await db.refresh(area)
    return area


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone_area(area_id: UUID, db: AsyncSession = Depends(get_db), _: str = Depends(require_admin)):
    result = await db.execute(select(ZoneArea).where(ZoneArea.id == area_id))
    area = result.scalar_one_or_none()
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    
    area.is_active = False
    await db.commit()