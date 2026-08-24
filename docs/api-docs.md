# API Documentation

Base URL: `http://localhost:8000/api`

Swagger UI: `http://localhost:8000/docs`

All protected endpoints require `Authorization: Bearer <access_token>`.

> **Source of truth:** FastAPI's generated OpenAPI schema at `/openapi.json` and Swagger UI at `/docs`. This Markdown document provides the evaluator-friendly API overview and representative request examples.

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "password123",
  "role": "customer"
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ..."
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

---

## Pricing

### Calculate Price
```http
POST /pricing/calculate
Authorization: Bearer <token>
Content-Type: application/json

{
  "length_cm": 30,
  "breadth_cm": 20,
  "height_cm": 15,
  "actual_weight_kg": 2.5,
  "order_type": "b2c",
  "payment_type": "cod",
  "pickup_zone_id": "uuid...",
  "drop_zone_id": "uuid...",
  "order_value": 3000
}
```

### Get Quote

```http
POST /pricing/quote
Authorization: Bearer <token>
Content-Type: application/json

{
  "length_cm": 30,
  "breadth_cm": 20,
  "height_cm": 15,
  "actual_weight_kg": 2.5,
  "order_type": "b2c",
  "payment_type": "cod",
  "pickup_pincode": "110001",
  "drop_pincode": "400001",
  "order_value": 3000
}
```

---

## Zone Detection

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/zones/detect` | Detect pickup/drop zones from pincodes |
| POST | `/zones/detect-by-pincode` | Detect a single zone |

Example:

```json
{
  "pickup_pincode": "110001",
  "pickup_city": "Delhi",
  "drop_pincode": "400001",
  "drop_city": "Mumbai"
}
```

---

## Customer Orders

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/orders` | Create order and calculate server-side pricing |
| POST | `/orders/quote` | Get quote before creating an order |
| GET | `/orders` | List customer's orders |
| GET | `/orders/{order_id}` | Get order details |
| GET | `/orders/number/{order_number}` | Get order by number |
| PATCH | `/orders/{order_id}/status` | Update an allowed status transition |
| GET | `/orders/{order_id}/tracking` | Get immutable tracking history |
| PATCH | `/orders/{order_id}` | Update permitted fields before pickup |
| DELETE | `/orders/{order_id}` | Cancel an eligible order |

### Create Order

```http
POST /orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "pickup_address": "123 Main St, Delhi",
  "pickup_pincode": "110001",
  "pickup_city": "Delhi",
  "drop_address": "456 Park Ave, Mumbai",
  "drop_pincode": "400001",
  "drop_city": "Mumbai",
  "length_cm": 30,
  "breadth_cm": 20,
  "height_cm": 15,
  "actual_weight_kg": 2.5,
  "order_type": "b2c",
  "payment_type": "cod",
  "order_value": 3000
}
```

### Status update

```http
PATCH /orders/{order_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "picked_up",
  "reason": "Package collected from warehouse"
}
```

The backend validates status transitions and role permissions. `ASSIGNED` is created by assignment; `PICKED_UP` is an explicit pickup event.

---

## Admin Endpoints

### Zones

| Method | Endpoint | Description |
|---|---|---|
| POST | `/admin/zones` | Create zone |
| GET | `/admin/zones` | List zones |
| GET | `/admin/zones/{id}` | Get zone |
| PUT | `/admin/zones/{id}` | Update zone, including optional center coordinates |
| DELETE | `/admin/zones/{id}` | Soft delete zone |
| POST | `/admin/zones/{id}/areas` | Add area to zone |
| GET | `/admin/zones/{id}/areas` | List zone areas |
| PUT | `/admin/areas/{id}` | Update area |
| DELETE | `/admin/areas/{id}` | Soft delete area |

### Rate Cards

| Method | Endpoint | Description |
|---|---|---|
| POST | `/admin/rate-cards` | Create rate card |
| GET | `/admin/rate-cards` | List rate cards |
| GET | `/admin/rate-cards/{id}` | Get rate card |
| PUT | `/admin/rate-cards/{id}` | Update rate card |
| DELETE | `/admin/rate-cards/{id}` | Soft delete rate card |
| POST | `/admin/rate-cards/{id}/rules` | Add rate rule |
| GET | `/admin/rate-cards/{id}/rules` | List rate rules |
| PUT | `/admin/rate-rules/{id}` | Update rate rule |
| DELETE | `/admin/rate-rules/{id}` | Delete rate rule |
| POST | `/admin/rate-cards/{id}/cod-surcharges` | Add COD surcharge |
| GET | `/admin/rate-cards/{id}/cod-surcharges` | List COD surcharges |
| PUT | `/admin/cod-surcharges/{id}` | Update COD surcharge |
| DELETE | `/admin/cod-surcharges/{id}` | Delete COD surcharge |

### Orders / Assignment

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/orders` | List all orders |
| GET | `/admin/orders/{id}` | Get order details |
| PATCH | `/admin/orders/{id}/status` | Update status through admin rules |
| POST | `/admin/orders/{id}/override` | Override status when authorized |
| POST | `/admin/assign` | Manual or automatic agent assignment/reassignment |

Auto-assignment ranks eligible agents by pickup-zone affinity, Haversine distance from the pickup-zone center, then current load.

### Agents

| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/agents` | List agents |
| GET | `/admin/agents/{id}` | Get agent |
| PATCH | `/admin/agents/{id}/deactivate` | Deactivate agent |

---

## Agent Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/agents/profile` | Create agent profile |
| GET | `/agents/profile` | Get current agent profile |
| PATCH | `/agents/profile` | Update profile |
| PATCH | `/agents/availability` | Update availability |
| POST | `/agents/location` | Update GPS location |
| GET | `/agent` | Agent dashboard |
| GET | `/agent/orders` | Assigned orders |
| GET | `/agent/orders/{id}` | Assigned order details |
| PATCH | `/agent/orders/{id}/status` | Update delivery status |
| POST | `/agent/orders/{id}/complete` | Complete delivery |

---

## Failed Deliveries & Rescheduling

### Mark Failed

```http
POST /failed-deliveries/{order_id}/mark-failed
Authorization: Bearer <token>
Content-Type: application/json

{
  "failure_reason": "Customer not available",
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

### Request Reschedule

```http
POST /failed-deliveries/{order_id}/reschedule
Authorization: Bearer <token>
Content-Type: application/json

{
  "preferred_date": "2026-08-25T10:00:00Z",
  "preferred_time_slot": "morning",
  "reason": "Was not home"
}
```

### Approve / Reject Reschedule

```http
PATCH /failed-deliveries/reschedule-requests/{id}/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "new_agent_id": "uuid..."
}
```

```http
PATCH /failed-deliveries/reschedule-requests/{id}/reject
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "No agents available"
}
```

---

## Order Statuses

| Status | Meaning |
|---|---|
| `created` | Order created, awaiting assignment |
| `assigned` | Agent selected, awaiting pickup |
| `picked_up` | Agent physically picked up the package |
| `in_transit` | Package moving toward destination |
| `out_for_delivery` | Final delivery attempt is in progress |
| `delivered` | Successfully delivered |
| `failed` | Current delivery attempt failed |
| `cancelled` | Order cancelled |

## Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

## Error Format

```json
{
  "detail": "Error description"
}
```

## Pagination and Filtering

Common list endpoints support:

- `skip`: number of records to skip
- `limit`: maximum records per page (max 100)
- `status`: filter by order status
- `order_type`: `b2b` or `b2c`
- `payment_type`: `prepaid` or `cod`
