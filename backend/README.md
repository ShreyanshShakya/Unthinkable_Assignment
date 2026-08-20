# Last Mile Delivery Tracker - Backend

FastAPI backend for the last-mile delivery tracking system.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Auth**: JWT with RS256
- **Validation**: Pydantic v2
- **Email**: Resend
- **SMS**: Twilio
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff + black
- **Type Checking**: mypy

## Project Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core config, security
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── db/            # Database session
│   └── utils/         # Utilities
├── migrations/        # Alembic migrations
├── tests/             # Test suite
├── pyproject.toml     # Dependencies
├── alembic.ini        # Alembic config
└── .env.example       # Environment template
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- uv (recommended) or pip

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your values
```

### Database

```bash
# Start PostgreSQL (if using docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Create initial migration (after model changes)
alembic revision --autogenerate -m "description"
```

### Running

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Linting & Formatting

```bash
# Check
ruff check .
black --check .

# Fix
ruff check . --fix
black .
```

### Type Checking

```bash
mypy app/
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key (32+ chars) | Yes |
| `DEBUG` | Enable debug mode | No |
| `ENVIRONMENT` | development/production/test | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `RESEND_API_KEY` | Resend API key for emails | No |
| `EMAIL_FROM` | Sender email address | No |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | No |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | No |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | No |
| `FRONTEND_URL` | Frontend URL for email links | No |

## API Documentation

- Swagger UI: http://localhost:8000/docs (dev only)
- ReDoc: http://localhost:8000/redoc (dev only)
- OpenAPI JSON: http://localhost:8000/openapi.json

## License

MIT