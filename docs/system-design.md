# Last Mile Delivery Tracker - System Design Document

## Overview
A comprehensive last-mile delivery tracking system with real-time order management, agent assignment, dynamic pricing, and notifications. Built with a modern tech stack: FastAPI (Python) backend, Next.js 14 (React) frontend, PostgreSQL database.

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
- **Zones & Areas**: Geographic coverage with pincode mapping
- **Rate Cards**: B2B/B2C, Intra/Inter-zone pricing with weight slabs
- **COD Surcharges**: Configurable percentage with min/max bounds
- **Orders**: Complete lifecycle with pricing snapshots
- **Status History**: Immutable audit trail with actor/timestamp/reason
- **Agents**: Profiles, availability, location tracking
- **Assignments**: Auto (nearest available) or manual by admin
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

### Order Lifecycle
```
CREATED → PICKED_UP → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED
                              ↘ FAILED → (reschedule) → OUT_FOR_DELIVERY
```

### Agent Assignment
- **Auto**: Nearest available agent in pickup zone (least busy first)
- **Manual**: Admin assigns specific agent
- **Capacity**: Max concurrent deliveries per agent (default 3)
- **States**: AVAILABLE / BUSY / OFFLINE with GPS location tracking

### Notifications
- **Triggers**: Every status change + agent assignment
- **Channels**: Email (Resend) + SMS (Twilio)
- **Templates**: Status-specific messages with tracking links

## API Design
- **RESTful** endpoints with consistent naming
- **Role-based access**: Customer / Agent / Admin
- **JWT authentication** with access/refresh tokens
- **OpenAPI/Swagger** documentation at `/docs`

## Security
- **Password hashing**: bcrypt via passlib
- **JWT tokens**: HS256 with configurable expiry
- **Role middleware**: Route-level authorization
- **Input validation**: Pydantic schemas on all endpoints
- **CORS**: Configurable origins

## Deployment
- **Frontend**: Vercel (Next.js)
- **Backend**: Render/Railway (FastAPI + Uvicorn)
- **Database**: Neon serverless PostgreSQL
- **Environment**: Docker Compose for local dev

## Scalability Considerations
- **Stateless API**: Horizontal scaling ready
- **Connection pooling**: SQLAlchemy async pool
- **Background tasks**: Can integrate Celery/Redis for notifications
- **Database indexes**: Optimized for common query patterns
- **Async throughout**: FastAPI + SQLAlchemy 2.0 async

## Tech Stack Summary
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 15 (Neon serverless) |
| Auth | JWT (HS256), bcrypt |
| Email | Resend API |
| SMS | Twilio API |
| Testing | pytest, Jest |
| CI/CD | GitHub Actions ready |

## Future Enhancements
- Real-time tracking with WebSockets
- Route optimization for agents
- Analytics dashboard
- Mobile app (React Native)
- Multi-tenant support