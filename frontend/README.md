# Last Mile Delivery Tracker - Frontend

Next.js 14 frontend for the last-mile delivery tracking system.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Testing**: Jest + React Testing Library
- **Linting**: ESLint + Next.js config

## Project Structure

```
frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # Reusable UI components
│   ├── lib/           # Utilities, API client
│   ├── hooks/         # Custom React hooks
│   ├── store/         # Zustand stores
│   └── types/         # TypeScript types
├── public/            # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── .env.example
```

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn or pnpm

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your values
```

### Running

```bash
# Development
npm run dev

# Production build
npm run build
npm start

# Linting
npm run lint

# Type checking
npm run type-check

# Testing
npm run test
npm run test:watch
npm run test:coverage
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |
| `NEXT_PUBLIC_APP_NAME` | Application name | No |

## Pages Structure (Planned)

```
/                     # Landing page
/login                # Login page
/register             # Registration page
/dashboard            # Role-based dashboard
/customer/
  /orders             # Customer order list
  /orders/new         # Create new order
  /orders/[id]        # Order details & tracking
  /profile            # Customer profile
/agent/
  /orders             # Assigned orders
  /orders/[id]        # Delivery details
  /availability       # Toggle availability
/admin/
  /orders             # All orders with filters
  /zones              # Zone management
  /areas              # Area management
  /rates              # Rate card configuration
  /cod                # COD surcharge config
  /agents             # Agent management
  /assignments        # Manual assignment
```

## API Integration

The frontend communicates with the backend via the API client in `src/lib/api.ts`. It includes:

- Automatic JWT token attachment
- Token refresh on 401 responses
- Type-safe request/response handling

## Components (Planned)

- `Button`, `Input`, `Select`, `Card` - Base UI components
- `OrderCard`, `OrderForm`, `TrackingTimeline` - Domain components
- `AuthGuard`, `RoleGuard` - Route protection
- `DataTable` - Reusable table with sorting/filtering

## License

MIT