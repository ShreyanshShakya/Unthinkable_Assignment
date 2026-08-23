# Last Mile Delivery Tracker

A complete last-mile delivery tracking system with real-time order management, agent assignment, pricing engine, and notifications.

## Architecture

```
┌─────────────┐     REST API      ┌─────────────┐
│  Frontend   │ ◄─────────────────► │  Backend    │
│  (Next.js)  │                     │  (FastAPI)  │
└─────────────┘                     └──────┬──────┘
                                            │
                                    ┌───────▼───────┐
                                    │  PostgreSQL   │
                                    │  (Neon/Local) │
                                    └───────────────┘
```

## Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0** - Async ORM
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **JWT** - Authentication
- **Resend** - Transactional emails
- **Twilio** - SMS notifications
- **Pytest** - Testing

### Frontend
- **Next.js 14** - React framework (App Router)
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Hook Form + Zod** - Forms & validation
- **Axios** - HTTP client

## Project Structure

```
last-mile-delivery-tracker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── db/             # Database session
│   ├── migrations/         # Alembic migrations
│   ├── tests/              # Test suite
│   └── pyproject.toml
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/            # App Router pages
│   │   ├── components/     # UI components
│   │   ├── lib/            # Utilities
│   │   ├── store/          # Zustand stores
│   │   └── types/          # TypeScript types
│   └── package.json
├── docker-compose.yml      # Full stack
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend dev)
- Python 3.11+ (for backend dev)

### With Docker (Recommended)

```bash
# Clone and navigate
cd last-mile-delivery-tracker

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit backend/.env with your values (SECRET_KEY, API keys, etc.)

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env
docker-compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Key Features

### Customer
- Create orders with real-time pricing
- Track deliveries with timeline
- Reschedule failed deliveries
- Email/SMS notifications

### Agent
- View assigned deliveries
- Update delivery status
- Toggle availability
- Location tracking

### Admin
- Manage zones & areas
- Configure rate cards (B2B/B2C, intra/inter-zone)
- Set COD surcharges
- Manual/auto agent assignment
- Override order status
- View all orders with filters

## Pricing Engine

The system calculates charges based on:
1. **Volumetric Weight** = L × B × H / 5000
2. **Billable Weight** = max(actual_weight, volumetric_weight)
3. **Base Charge** = from rate card (based on zone type & order type)
4. **COD Surcharge** = percentage of order value (configurable)
5. **Total** = Base Charge + COD Surcharge

## Deployment

### Backend → Render/Railway
```bash
# Build and push to registry, or connect GitHub repo
# Set environment variables in dashboard
# Run migrations on deploy
```

### Frontend → Vercel
```bash
# Connect GitHub repo
# Set NEXT_PUBLIC_API_URL to production backend URL
# Deploy
```

### Database → Neon
```bash
# Create Neon project
# Get connection string
# Set as DATABASE_URL
# Run migrations
```

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [System Design](docs/system-design.md)

## Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# E2E tests
# Run with: pytest tests/test_integration.py -v
```

## License

MIT