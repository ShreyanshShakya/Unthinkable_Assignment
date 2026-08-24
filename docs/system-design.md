# Last Mile Delivery Tracker — System Design

## 1. Overview

A last-mile delivery management system covering order creation, server-side pricing, pincode-based zone detection, agent assignment, delivery tracking, failed-delivery rescheduling, and email/SMS notifications.

## 2. Architecture

```mermaid
flowchart TB
    subgraph Clients[Clients]
        C[Customer]
        AG[Delivery Agent]
        AD[Administrator]
    end

    subgraph Web[Application Layer]
        FE[Next.js 14 Frontend]
        API[FastAPI REST API]
    end

    subgraph Services[Business Services]
        AUTH[Auth / RBAC]
        ORDER[Order Service]
        PRICE[Pricing Engine]
        ZONE[Zone Detection]
        ASSIGN[Assignment Service]
        DELIVERY[Delivery / Reschedule]
        NOTIFY[Notification Service]
    end

    DB[(PostgreSQL / Neon)]
    REDIS[(Redis)]
    EMAIL[Resend]
    SMS[Twilio]

    C --> FE
    AG --> FE
    AD --> FE
    FE <--> |REST + JWT| API
    API --> AUTH
    API --> ORDER
    API --> PRICE
    API --> ZONE
    API --> ASSIGN
    API --> DELIVERY
    API --> NOTIFY
    AUTH --> DB
    ORDER --> DB
    PRICE --> DB
    ZONE --> DB
    ASSIGN --> DB
    DELIVERY --> DB
    NOTIFY --> DB
    NOTIFY --> EMAIL
    NOTIFY --> SMS
    NOTIFY -. optional background work .-> REDIS
```

The API is stateless. PostgreSQL is the system of record; Neon PostgreSQL is the production database. Docker Compose is used for local development, and PostgreSQL Testcontainers is used for integration tests.

## 3. Core Data Model

```mermaid
erDiagram
    USER ||--o{ ORDER : creates
    USER ||--o| AGENT : has_profile
    ZONE ||--o{ ZONE_AREA : contains
    ZONE ||--o{ AGENT : serves
    ZONE ||--o{ RATE_CARD_RULE : pickup_or_drop
    AGENT ||--o| AGENT_LOCATION : reports
    ORDER ||--o{ ORDER_STATUS_HISTORY : records
    ORDER ||--o| DELIVERY_ASSIGNMENT : assigned
    ORDER ||--o{ DELIVERY_ATTEMPT : has
    ORDER ||--o{ RESCHEDULE_REQUEST : receives
    USER ||--o{ ORDER_STATUS_HISTORY : acts
    AGENT ||--o{ DELIVERY_ATTEMPT : performs
    RATE_CARD ||--o{ RATE_CARD_RULE : contains
    RATE_CARD ||--o{ COD_SURCHARGE : configures

    USER {
        uuid id PK
        string email
        string role
    }
    ZONE {
        uuid id PK
        string code
        decimal latitude
        decimal longitude
    }
    ZONE_AREA {
        uuid id PK
        uuid zone_id FK
        string pincode
    }
    ORDER {
        uuid id PK
        uuid customer_id FK
        uuid agent_id FK
        uuid pickup_zone_id FK
        uuid drop_zone_id FK
        string status
        decimal billable_weight_kg
        decimal total_charge
    }
    AGENT {
        uuid id PK
        uuid user_id FK
        uuid zone_id FK
        string status
        int current_deliveries_count
        int max_concurrent_deliveries
    }
    AGENT_LOCATION {
        uuid id PK
        uuid agent_id FK
        decimal latitude
        decimal longitude
    }
    RATE_CARD {
        uuid id PK
        string order_type
        string zone_type
        boolean is_active
    }
    RATE_CARD_RULE {
        uuid id PK
        uuid rate_card_id FK
        uuid pickup_zone_id FK
        uuid drop_zone_id FK
        decimal min_weight_kg
        decimal max_weight_kg
        decimal base_charge
        decimal per_kg_charge
    }
    COD_SURCHARGE {
        uuid id PK
        uuid rate_card_id FK
        decimal surcharge_percentage
        decimal min_surcharge
        decimal max_surcharge
    }
    ORDER_STATUS_HISTORY {
        uuid id PK
        uuid order_id FK
        string old_status
        string new_status
        uuid actor_id FK
        timestamp created_at
    }
    DELIVERY_ASSIGNMENT {
        uuid id PK
        uuid order_id FK
        uuid agent_id FK
        boolean is_auto_assigned
    }
    DELIVERY_ATTEMPT {
        uuid id PK
        uuid order_id FK
        uuid agent_id FK
        int attempt_number
        string status
    }
    RESCHEDULE_REQUEST {
        uuid id PK
        uuid order_id FK
        string status
        timestamp preferred_date
    }
```

## 4. Pricing Flow

```mermaid
flowchart LR
    D[Dimensions] --> VW[Volumetric Weight<br/>L × B × H / 5000]
    W[Actual Weight] --> BW[Billable Weight<br/>max(actual, volumetric)]
    VW --> BW
    P[Pincodes] --> Z[Pickup + Drop Zones]
    Z --> ZT[Intra / Inter Zone]
    BW --> RR[Rate Card Rule]
    ZT --> RR
    OT[Order Type<br/>B2B / B2C] --> RR
    RR --> BASE[Base + Per-kg Charge]
    PAY[Payment Type] --> COD{COD?}
    OV[Order Value] --> COD
    COD --> SUR[COD Surcharge<br/>percentage + min/max]
    BASE --> TOTAL[Total Charge]
    SUR --> TOTAL
```

### Pricing rules

- Volumetric weight = `L × B × H / 5000`.
- Billable weight = `max(actual weight, volumetric weight)`.
- Zone type is intra-zone when pickup and drop zones match; otherwise inter-zone.
- Rate selection considers order type, zone type, active status, effective dates, pickup/drop zones, and weight slab.
- COD surcharge is applied only to COD orders and is bounded by configured minimum/maximum values.
- Pricing is calculated server-side and the resulting values are stored with the order so later rate-card changes do not rewrite historical order pricing.

## 5. Order Lifecycle

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> ASSIGNED : agent assigned
    ASSIGNED --> PICKED_UP : agent picks up
    PICKED_UP --> IN_TRANSIT : dispatch
    IN_TRANSIT --> OUT_FOR_DELIVERY : final-mile dispatch
    OUT_FOR_DELIVERY --> DELIVERED : successful delivery
    OUT_FOR_DELIVERY --> FAILED : delivery attempt fails
    FAILED --> ASSIGNED : reschedule approved / reassigned
    CREATED --> CANCELLED : customer/admin cancellation
    FAILED --> CANCELLED : cancellation
    DELIVERED --> [*]
    CANCELLED --> [*]
```

`ASSIGNED` is a first-class order status. It records agent selection and is intentionally distinct from `PICKED_UP`, which is an explicit delivery-agent action.

## 6. Agent Assignment

```mermaid
flowchart TD
    START[Order requires assignment] --> FILTER[Filter agents]
    FILTER --> ELIGIBLE{Active + Available + Below Capacity?}
    ELIGIBLE -->|No| NEXT[Exclude agent]
    ELIGIBLE -->|Yes| ZONE{Same pickup zone?}
    ZONE --> RANK[Rank candidates]
    ZONE --> FALLBACK[Consider eligible agents in other zones]
    FALLBACK --> RANK
    RANK --> DIST[Haversine distance<br/>Zone center → latest agent location]
    DIST --> LOAD[Current delivery load]
    LOAD --> SELECT[Select highest-ranked candidate]
    SELECT --> ASSIGN[Create assignment + status history]
    ASSIGN --> STATUS[Order = ASSIGNED]
```

Ranking order is deterministic:

1. Pickup-zone affinity.
2. Haversine distance from the pickup-zone center to the agent's latest known location.
3. Current delivery load.

Agents at or above `max_concurrent_deliveries`, inactive agents, and unavailable agents are excluded. Zone coordinates are a single optional center point per zone for the MVP.

## 7. Failed Delivery and Rescheduling

```mermaid
flowchart LR
    OFD[OUT_FOR_DELIVERY] --> FAIL[FAILED]
    FAIL --> ATTEMPT[Record Delivery Attempt]
    ATTEMPT --> CUSTOMER[Customer requests reschedule]
    CUSTOMER --> ADMIN[Admin reviews request]
    ADMIN -->|Reject| END[Request rejected]
    ADMIN -->|Approve| REASSIGN[Assign eligible agent]
    REASSIGN --> ASSIGNED[ASSIGNED]
    ASSIGNED --> PICKUP[PICKED_UP]
```

Each failed attempt is retained. Rescheduling creates an auditable request and can result in a new assignment/attempt.

## 8. Status History and Auditability

Every status transition records:

- order
- previous status
- new status
- actor
- actor role
- timestamp
- optional reason/context

The history is append-only from the application workflow and is used as the tracking/audit trail.

## 9. Notifications

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant DB as PostgreSQL
    participant N as Notification Service
    participant E as Resend
    participant S as Twilio

    API->>DB: Commit business event
    API->>N: Trigger notification
    N->>E: Send email
    N->>S: Send SMS
    E-->>N: Provider result
    S-->>N: Provider result
    N->>DB: Persist notification status
```

Notification-provider failure is tracked separately and should not invalidate a successful order/delivery transaction.

## 10. Security

- Password hashing using bcrypt/passlib.
- JWT access/refresh tokens.
- Role-based route authorization for Customer, Agent and Admin.
- Pydantic request validation.
- Configurable CORS origins.
- Secrets supplied through environment variables.

## 11. Testing Strategy

```mermaid
flowchart TB
    UNIT[Unit Tests<br/>pricing, validation, state rules] --> INT[Integration Tests<br/>PostgreSQL + Testcontainers]
    INT --> E2E[Critical E2E Workflows]
    E2E --> DEPLOY[Production Verification]
```

Integration tests use PostgreSQL through Testcontainers so database behavior is close to production. Critical workflows cover order creation, assignment, delivery progression, and failed-delivery/rescheduling.

## 12. Deployment

- **Frontend:** Vercel / Next.js
- **Backend:** Render or Railway / FastAPI + Uvicorn
- **Database:** Neon PostgreSQL
- **Local:** Docker Compose
- **Integration tests:** PostgreSQL Testcontainers

## 13. Scalability and Future Enhancements

The API is stateless and can scale horizontally. SQLAlchemy async connection pooling and indexed PostgreSQL queries support the current workload. Redis/Celery can be introduced for heavier asynchronous processing.

Future enhancements:
- WebSocket-based real-time tracking
- Route optimization
- Analytics dashboards
- React Native mobile client
- Multi-tenant architecture
