from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from typing import List, Optional
from app.db.session import get_db
from app.services.agent import AgentService, get_agent_service
from app.schemas.agent import (
    AgentProfileCreate, AgentProfileUpdate, AgentProfileResponse,
    AgentLocationUpdate, AgentLocationResponse,
    AgentAvailabilityUpdate, AssignmentRequest, AssignmentResponse,
    NearbyAgent
)
from app.api.deps import require_agent, require_admin, get_current_user
from app.models import User, UserRole, AgentStatus, OrderStatus, Agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/profile", response_model=AgentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_profile(
    profile_data: AgentProfileCreate,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Create agent profile for current user"""
    # Check if profile already exists
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Agent profile already exists")
    
    agent = Agent(
        id=uuid4(),
        user_id=current_user.id,
        employee_id=profile_data.employee_id,
        zone_id=profile_data.zone_id,
        max_concurrent_deliveries=profile_data.max_concurrent_deliveries,
        status=AgentStatus.OFFLINE,
    )
    agent_service.db.add(agent)
    await agent_service.db.commit()
    await agent_service.db.refresh(agent)
    return agent


@router.get("/profile", response_model=AgentProfileResponse)
async def get_my_profile(
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Get current user's agent profile"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent)
        .options(selectinload(Agent.user))
        .where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    # Build response with user info
    return AgentProfileResponse(
        id=agent.id,
        user_id=agent.user_id,
        employee_id=agent.employee_id,
        zone_id=agent.zone_id,
        status=agent.status,
        max_concurrent_deliveries=agent.max_concurrent_deliveries,
        current_deliveries_count=agent.current_deliveries_count,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        user_email=agent.user.email if agent.user else None,
        user_name=agent.user.full_name if agent.user else None,
        user_phone=agent.user.phone if agent.user else None,
    )


@router.patch("/profile", response_model=AgentProfileResponse)
async def update_my_profile(
    profile_data: AgentProfileUpdate,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Update current user's agent profile"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    
    await agent_service.db.commit()
    await agent_service.db.refresh(agent)
    return agent


@router.patch("/availability", response_model=AgentProfileResponse)
async def update_availability(
    availability: AgentAvailabilityUpdate,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Update agent availability status"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    agent.status = availability.status
    await agent_service.db.commit()
    await agent_service.db.refresh(agent)
    return agent


@router.post("/location", response_model=AgentLocationResponse)
async def update_location(
    location: AgentLocationUpdate,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Update agent's current location"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    updated_location = await agent_service.update_agent_location(
        agent_id=agent.id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy_meters=location.accuracy_meters
    )
    return updated_location


@router.get("/dashboard")
async def get_dashboard(
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Get agent dashboard with active orders and stats"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    dashboard = await agent_service.get_agent_dashboard(agent.id)
    return dashboard


@router.get("/nearby")
async def find_nearby_agents(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    max_distance_km: float = Query(50.0, ge=1, le=200),
    limit: int = Query(10, ge=1, le=50),
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """Find nearby available agents (admin only)"""
    agents = await agent_service.find_nearest_available_agents(
        pickup_latitude=latitude,
        pickup_longitude=longitude,
        max_distance_km=max_distance_km,
        limit=limit
    )
    return agents


# Admin endpoints
@router.get("", response_model=List[AgentProfileResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[AgentStatus] = None,
    zone_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """List all agents (admin only)"""
    from app.models import Agent
    query = select(Agent).options(selectinload(Agent.user))
    
    if status:
        query = query.where(Agent.status == status)
    if zone_id:
        query = query.where(Agent.zone_id == zone_id)
    if is_active is not None:
        query = query.where(Agent.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())
    result = await agent_service.db.execute(query)
    agents = result.scalars().all()
    
    return [
        AgentProfileResponse(
            id=a.id,
            user_id=a.user_id,
            employee_id=a.employee_id,
            zone_id=a.zone_id,
            status=a.status,
            max_concurrent_deliveries=a.max_concurrent_deliveries,
            current_deliveries_count=a.current_deliveries_count,
            is_active=a.is_active,
            created_at=a.created_at,
            updated_at=a.updated_at,
            user_email=a.user.email if a.user else None,
            user_name=a.user.full_name if a.user else None,
            user_phone=a.user.phone if a.user else None,
        )
        for a in agents
    ]


@router.post("/assign", response_model=AssignmentResponse)
async def assign_order(
    assignment: AssignmentRequest,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """Assign order to agent (manual or auto)"""
    if assignment.agent_id:
        # Manual assignment
        result = await agent_service.manual_assign_order(
            order_id=assignment.order_id,
            agent_id=assignment.agent_id,
            admin_id=current_user.id
        )
    else:
        # Auto assignment
        result = await agent_service.auto_assign_order(assignment.order_id)
        if not result:
            raise HTTPException(status_code=404, detail="No available agents found")
    
    return result


@router.post("/reassign", response_model=AssignmentResponse)
async def reassign_order(
    order_id: UUID,
    new_agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """Reassign order to different agent"""
    result = await agent_service.reassign_order(
        order_id=order_id,
        new_agent_id=new_agent_id,
        admin_id=current_user.id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found or not assigned")
    return result


@router.post("/{agent_id}/complete-delivery/{order_id}")
async def complete_delivery(
    agent_id: UUID,
    order_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_agent)
):
    """Mark delivery as completed"""
    # Verify this agent owns the order
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    agent = result.scalar_one_or_none()
    if not agent or agent.id != agent_id:
        raise HTTPException(status_code=403, detail="Not authorized for this agent")
    
    success = await agent_service.complete_delivery(order_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"success": True, "message": "Delivery completed"}


@router.get("/{agent_id}", response_model=AgentProfileResponse)
async def get_agent(
    agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """Get agent by ID (admin only)"""
    from app.models import Agent
    result = await agent_service.db.execute(
        select(Agent).options(selectinload(Agent.user)).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentProfileResponse(
        id=agent.id,
        user_id=agent.user_id,
        employee_id=agent.employee_id,
        zone_id=agent.zone_id,
        status=agent.status,
        max_concurrent_deliveries=agent.max_concurrent_deliveries,
        current_deliveries_count=agent.current_deliveries_count,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        user_email=agent.user.email if agent.user else None,
        user_name=agent.user.full_name if agent.user else None,
        user_phone=agent.user.phone if agent.user else None,
    )


@router.patch("/{agent_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_agent(
    agent_id: UUID,
    agent_service: AgentService = Depends(get_agent_service),
    current_user: User = Depends(require_admin)
):
    """Deactivate agent (admin only)"""
    from app.models import Agent
    result = await agent_service.db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.is_active = False
    agent.status = AgentStatus.OFFLINE
    await agent_service.db.commit()