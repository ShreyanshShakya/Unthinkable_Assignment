from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Zone, ZoneArea


class ZoneDetectionService:
    """Service for detecting zones based on address/pincode"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_zone_by_pincode(self, pincode: str) -> Optional[Zone]:
        """Detect zone by pincode"""
        # Normalize pincode
        pincode = pincode.strip().upper()

        # First try exact pincode match
        result = await self.db.execute(
            select(ZoneArea, Zone)
            .join(Zone, ZoneArea.zone_id == Zone.id)
            .where(ZoneArea.pincode == pincode)
            .where(ZoneArea.is_active == True)
            .where(Zone.is_active == True)
        )
        row = result.first()
        if row:
            return row.Zone

        # Try prefix match (e.g., first 3 digits for broader area)
        if len(pincode) >= 3:
            prefix = pincode[:3]
            result = await self.db.execute(
                select(ZoneArea, Zone)
                .join(Zone, ZoneArea.zone_id == Zone.id)
                .where(ZoneArea.pincode.like(f"{prefix}%"))
                .where(ZoneArea.is_active == True)
                .where(Zone.is_active == True)
                .order_by(ZoneArea.pincode)
                .limit(1)
            )
            row = result.first()
            if row:
                return row.Zone

        return None

    async def detect_zone_by_address(self, address: str, city: Optional[str] = None, state: Optional[str] = None) -> Optional[Zone]:
        """Detect zone by address components"""
        # Try to extract pincode from address (assuming Indian pincode format)
        import re
        pincode_match = re.search(r'\b\d{6}\b', address)
        if pincode_match:
            zone = await self.detect_zone_by_pincode(pincode_match.group())
            if zone:
                return zone

        # Fallback to city/state matching
        if city:
            result = await self.db.execute(
                select(ZoneArea, Zone)
                .join(Zone, ZoneArea.zone_id == Zone.id)
                .where(ZoneArea.city.ilike(f"%{city}%"))
                .where(ZoneArea.is_active == True)
                .where(Zone.is_active == True)
                .limit(1)
            )
            row = result.first()
            if row:
                return row.Zone

        if state:
            result = await self.db.execute(
                select(ZoneArea, Zone)
                .join(Zone, ZoneArea.zone_id == Zone.id)
                .where(ZoneArea.state.ilike(f"%{state}%"))
                .where(ZoneArea.is_active == True)
                .where(Zone.is_active == True)
                .limit(1)
            )
            row = result.first()
            if row:
                return row.Zone

        return None

    async def get_pickup_drop_zones(
        self,
        pickup_pincode: str,
        drop_pincode: str,
        pickup_city: Optional[str] = None,
        pickup_state: Optional[str] = None,
        drop_city: Optional[str] = None,
        drop_state: Optional[str] = None
    ) -> tuple[Optional[Zone], Optional[Zone]]:
        """Get both pickup and drop zones"""
        pickup_zone = await self.detect_zone_by_pincode(pickup_pincode)
        if not pickup_zone and pickup_city:
            pickup_zone = await self.detect_zone_by_address("", city=pickup_city, state=pickup_state)

        drop_zone = await self.detect_zone_by_pincode(drop_pincode)
        if not drop_zone and drop_city:
            drop_zone = await self.detect_zone_by_address("", city=drop_city, state=drop_state)

        return pickup_zone, drop_zone

    async def determine_zone_type(self, pickup_zone_id: UUID, drop_zone_id: UUID) -> str:
        """Determine if delivery is intra-zone or inter-zone"""
        from app.models import ZoneType
        if pickup_zone_id == drop_zone_id:
            return ZoneType.INTRA_ZONE.value
        return ZoneType.INTER_ZONE.value


async def get_zone_detection_service(db: AsyncSession = Depends(get_db)) -> ZoneDetectionService:
    return ZoneDetectionService(db)
