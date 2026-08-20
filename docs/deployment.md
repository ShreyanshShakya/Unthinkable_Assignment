# Deployment Guide

## Prerequisites
- Docker & Docker Compose
- Git
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)

## Local Development

### Quick Start with Docker
```bash
# Clone repository
git clone <repo-url>
cd last-mile-delivery-tracker

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit backend/.env with your values (SECRET_KEY, API keys, etc.)

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (without Docker)

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your values

# Start PostgreSQL (required)
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local if needed
npm run dev
```

## Production Deployment

### Database (Neon PostgreSQL)
1. Create account at https://neon.tech
2. Create new project
3. Copy connection string
3. Set as `DATABASE_URL` in backend environment

### Backend (Render/Railway)

#### Render
1. Connect GitHub repository
2. Create new Web Service
3. Build command: `pip install -e ".[dev]"`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Add `alembic upgrade head` as pre-deploy command

#### Railway
1. Connect GitHub repository
2. Add PostgreSQL plugin (or use Neon)
3. Set environment variables
4. Deploy

### Frontend (Vercel)
1. Import GitHub repository
2. Set `NEXT_PUBLIC_API_URL` to production backend URL
3. Deploy

## Environment Variables

### Backend (.env)
```env
# App
APP_NAME="Last Mile Delivery Tracker"
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Security
SECRET_KEY=your-32-char-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://your-frontend.vercel.app"]

# Email (Resend)
RESEND_API_KEY=re_xxxxx
EMAIL_FROM=noreply@yourdomain.com

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxx
TWILIO_PHONE_NUMBER=+1xxx

# Frontend URL
FRONTEND_URL=https://your-frontend.vercel.app
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_APP_NAME="Last Mile Delivery Tracker"
```

## Post-Deployment

### Database Setup
```bash
# Run migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed.py
```

### Verify Deployment
1. Check health: `GET /health`
2. Test auth: Register/login
3. Create test order
4. Verify pricing calculation
5. Test agent assignment
6. Test notifications

## Monitoring
- Health endpoint: `/health`
- Logs: Structured JSON logging
- Metrics: Add Prometheus if needed

## Rollback
```bash
# Database rollback
alembic downgrade -1

# Code rollback
git revert <commit>
# Redeploy
```

## Security Checklist
- [ ] Strong SECRET_KEY (32+ chars)
- [ ] DEBUG=false in production
- [ ] HTTPS only
- [ ] CORS origins restricted
- [ ] Database credentials rotated
- [ ] API keys secured
- [ ] Rate limiting enabled