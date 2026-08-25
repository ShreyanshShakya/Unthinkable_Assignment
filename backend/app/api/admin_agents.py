from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models import Agent, AgentStatus, User, UserRole
from app.schemas.agent import AgentProfileResponse

router = APIRouter(prefix="/admin/agents", tags=["admin-agents"])


class AdminAgentCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)


class AdminAgentProfileCreate(BaseModel):
    user_id: UUID
    employee_id: str = Field(min_length=1, max_length=50)
    zone_id: UUID | None = None
    max_concurrent_deliveries: int = Field(default=3, ge=1, le=10)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent_account(data: AdminAgentCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(id=uuid4(), email=data.email, hashed_password=get_password_hash(data.password), full_name=data.full_name, phone=data.phone, role=UserRole.AGENT)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "user_id": user.id, "email": user.email, "role": user.role}


@router.post("/profile", response_model=AgentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_profile(data: AdminAgentProfileCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    user_result = await db.execute(select(User).where(User.id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.role != UserRole.AGENT:
        raise HTTPException(status_code=400, detail="Agent user not found")
    existing = await db.execute(select(Agent).where(Agent.user_id == data.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent profile already exists")
    employee = await db.execute(select(Agent).where(Agent.employee_id == data.employee_id))
    if employee.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    agent = Agent(id=uuid4(), user_id=user.id, employee_id=data.employee_id, zone_id=data.zone_id, max_concurrent_deliveries=data.max_concurrent_deliveries, status=AgentStatus.OFFLINE)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return AgentProfileResponse(id=agent.id, user_id=agent.user_id, employee_id=agent.employee_id, zone_id=agent.zone_id, status=agent.status, max_concurrent_deliveries=agent.max_concurrent_deliveries, current_deliveries_count=agent.current_deliveries_count, is_active=agent.is_active, created_at=agent.created_at, updated_at=agent.updated_at, user_email=user.email, user_name=user.full_name, user_phone=user.phone)
