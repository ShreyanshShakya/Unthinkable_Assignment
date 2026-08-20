from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.zone_detection import ZoneDetectionService, get_zone_detection_service
from app.schemas.zone_detection import ZoneDetectionRequest, ZoneDetectionResponse, ZoneByPincodeRequest, ZoneByPincodeResponse
from app.schemas.zone import ZoneResponse
from app.api.deps import require_customer, require_agent, require_admin
from app.models import User

router = APIRouter(prefix="/zones", tags=["zone-detection"])


@router.post("/detect", response_model=ZoneDetectionResponse)
async def detect_zones(
    request: ZoneDetectionRequest,
    zone_service: ZoneDetectionService = Depends(get_zone_detection_service),
    current_user: User = Depends(require_customer)
):
    """Detect pickup and drop zones from address/pincode"""
    pickup_zone, drop_zone = await zone_service.get_pickup_drop_zones(
        pickup_pincode=request.pickup_pincode,
        pickup_city=request.pickup_city,
        pickup_state=request.pickup_state,
        drop_pincode=request.drop_pincode,
        drop_city=request.drop_city,
        drop_state=request.drop_state
    )
    
    zone_type = None
    if pickup_zone and drop_zone:
        zone_type = await zone_service.determine_zone_type(pickup_zone.id, drop_zone.id)
    
    return ZoneDetectionResponse(
        pickup_zone=ZoneInfo(id=pickup_zone.id, name=pickup_zone.name, code=pickup_zone.code) if pickup_zone else None,
        drop_zone=ZoneInfo(id=drop_zone.id, name=drop_zone.name, code=drop_zone.code) if drop_zone else None,
        zone_type=zone_type
    )


@router.post("/detect-by-pincode", response_model=ZoneByPincodeResponse)
async def detect_zone_by_pincode(
    request: ZoneByPincodeRequest,
    zone_service: ZoneDetectionService = Depends(get_zone_detection_service),
    current_user: User = Depends(require_customer)
):
    """Detect zone by pincode only"""
    zone = await zone_service.detect_zone_by_pincode(request.pincode)
    
    if zone:
        return ZoneByPincodeResponse(
            zone=ZoneInfo(id=zone.id, name=zone.name, code=zone.code),
            found=True
        )
    return ZoneByPincodeResponse(zone=None, found=False)


@router.get("/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_customer)
):
    """Get zone details by ID"""
    from uuid import UUID
    from sqlalchemy import select
    from app.models import Zone
    
    result = await db.execute(select(Zone).where(Zone.id == UUID(zone_id)))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone