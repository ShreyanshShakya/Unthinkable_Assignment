# Last Mile Delivery Tracker - System Design Document

## Overview
A comprehensive last-mile delivery tracking system with real-time order management, agent assignment, dynamic pricing, and notifications. Built with FastAPI (Python) backend, Next.js 14 frontend, and PostgreSQL.

## Architecture

```
┌─────────────────┐     REST API      ┌─────────────────┐
│   Frontend      │ ◄────────────────► │   Backend       │
│   (Next.js 14)  │                    │   (FastAPI)     │
└─────────────────┘                    └────────┬────────┘
                                                │
                                        ┌───────▼───────┐
                                        │  PostgreSQL   │
                                        │   (Neon)      │
                                        └───────────────┘
```

## Database Design

### Core Entities
- **Users**: Customers, Agents, Admins with role-based access
- **Zones & Areas**: Geographic coverage with pincode mapping and optional zone-center coordinates
- **Rate Cards**: B2B/B2C, Intra/Inter-zone pricing with weight slabs
- **COD Surcharges**: Configurable percentage with min/max bounds
- **Orders**: Complete lifecycle with pricing snapshots
- **Status History**: Immutable audit trail with actor/timestamp/reason
- **Agents**: Profiles, availability, location tracking
- **Assignments**: Auto or manual assignment with capacity checks
- **Delivery Attempts**: Track multiple attempts per order
- **Notifications**: Email (Resend) + SMS (Twilio) with delivery tracking
- **Reschedule Requests**: Customer-driven with admin approval

## Key Features

### Pricing Engine
- **Volumetric Weight**: L × B × H / 5000
- **Billable Weight**: max(actual, volumetric)
- **Zone Detection**: Pincode → Zone mapping (exact + prefix fallback)
- **Rate Lookup**: Order type × Zone type × Weight slab
- **COD Surcharge**: Percentage of order value with configurable caps
- Pricing values use decimal-safe calculations and are persisted with the order.

### Order Lifecycle
```
CREATED → ASSIGNED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
                              ↘ FAILED → (reschedule) → ASSIGNED → PICKED_UP
```

`ASSIGNED` means an agent has been selected but has not yet physically picked up the package. `PICKED_UP` is an explicit agent-driven transition.

### Agent Assignment
- **Auto**: Filters active/available agents below capacity, prefers agents in the pickup zone, then ranks by distance from the pickup-zone center and current load.
- **Manual**: Admin assigns a specific eligible agent.
- **Capacity**: Max concurrent deliveries per agent (default 3).
- **Distance**: Haversine distance between the pickup-zone center and the agent's latest known GPS location.
- **Fallback**: If no eligible same-zone agent exists, eligible agents in other zones can be considered.
- **States**: AVAILABLE / BUSY / OFFLINE with GPS location tracking.

### Notifications
- **Triggers**: Status changes and agent assignment.
- **Channels**: Email (Resend) + SMS (Twilio).
- **Templates**: Status-specific messages with tracking links.
- Notification failures are tracked independently so a provider failure does not invalidate a successful delivery transaction.

## API Design
- RESTful endpoints with consistent naming
- Role-based access: Customer / Agent / Admin
- JWT authentication with access/refresh tokens
- OpenAPI/Swagger documentation at `/docs`

## Security
- Password hashing via passlib/bcrypt
- JWT tokens with configurable expiry
- Route-level role authorization
- Pydantic input validation
- Configurable CORS origins

## Deployment
- **Frontend**: Vercel (Next.js)
- **Backend**: Render/Railway (FastAPI + Uvicorn)
- **Database**: Neon PostgreSQL
- **Local development**: Docker Compose
- **Integration tests**: PostgreSQL through Testcontainers

## Testing
- Unit tests cover pricing, status transitions, validation, and assignment ranking.
- Integration tests use PostgreSQL/Testcontainers to match production database behavior.
- Critical workflows cover order creation, assignment, delivery lifecycle, and failed-delivery/rescheduling behavior.

## Scalability Considerations
- Stateless API: horizontal scaling ready
- SQLAlchemy async connection pooling
- Background tasks can integrate Celery/Redis for notifications
- Database indexes optimized for common query patterns
- Async FastAPI + SQLAlchemy 2.0

## Tech Stack Summary
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 15 (Neon serverless) |
| Auth | JWT (HS256), bcrypt |
| Email | Resend API |
| SMS | Twilio API |
| Testing | pytest, PostgreSQL/Testcontainers |
| API Docs | OpenAPI / Swagger UI |

## Future Enhancements
- Real-time tracking with WebSockets
- Route optimization for agents
- Analytics dashboard
- Mobile app (React Native)
- Multi-tenant support
