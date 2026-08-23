# API Documentation

Base URL: `http://localhost:8000/api`
Swagger UI: `http://localhost:8000/docs`

## Authentication

All protected endpoints require `Authorization: Bearer <access_token>` header.

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

**Response**:
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

### Calculate Price (with zone IDs)
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

### Get Quote (with pincodes)
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

### Detect Zones
```http
POST /zones/detect
Authorization: Bearer <token>
Content-Type: application/json

{
  "pickup_pincode": "110001",
  "pickup_city": "Delhi",
  "drop_pincode": "400001",
  "drop_city": "Mumbai"
}
```

### Detect Single Zone by Pincode
```http
POST /zones/detect-by-pincode
Authorization: Bearer <token>
Content-Type: application/json

{
  "pincode": "110001"
}
```

---

## Customer Orders

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

### Get Quote Before Order
```http
POST /orders/quote
Authorization: Bearer <token>
Content-Type: application/json
```

### List Orders
```http
GET /orders?status=created&skip=0&limit=20
Authorization: Bearer <token>
```

### Get Order Details
```http
GET /orders/{order_id}
Authorization: Bearer <token>
```

### Get Order by Number
```http
GET /orders/number/{order_number}
Authorization: Bearer <token>
```

### Update Order Status (Customer/Agent)
```http
PATCH /orders/{order_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "picked_up",
  "reason": "Package collected from warehouse"
}
```

### Get Tracking History
```http
GET /orders/{order_id}/tracking
Authorization: Bearer <token>
```

### Update Order (before pickup)
```http
PATCH /orders/{order_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "drop_address": "Updated address",
  "order_value": 3500
}
```

### Cancel Order
```http
DELETE /orders/{order_id}
Authorization: Bearer <token>
```

---

## Admin Endpoints

### Zones

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/zones` | Create zone |
| GET | `/admin/zones` | List zones |
| GET | `/admin/zones/{id}` | Get zone |
| PUT | `/admin/zones/{id}` | Update zone |
| DELETE | `/admin/zones/{id}` | Soft delete zone |
| POST | `/admin/zones/{id}/areas` | Add area to zone |
| GET | `/admin/zones/{id}/areas` | List zone areas |
| PUT | `/admin/areas/{id}` | Update area |
| DELETE | `/admin/areas/{id}` | Soft delete area |

### Rate Cards

| Method | Endpoint | Description |
|--------|----------|-------------|
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

### Orders (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/orders` | List all orders |
| GET | `/admin/orders/{id}` | Get order details |
| PATCH | `/admin/orders/{id}/status` | Update status (any transition) |
| POST | `/admin/orders/{id}/override` | Override status (bypass validation) |
| POST | `/admin/assign` | Assign/reassign agent |

### Agents (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/agents` | List agents |
| GET | `/admin/agents/{id}` | Get agent |
| PATCH | `/admin/agents/{id}/deactivate` | Deactivate agent |

---

## Agent Endpoints

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/profile` | Create agent profile |
| GET | `/agents/profile` | Get my profile |
| PATCH | `/agents/profile` | Update profile |
| PATCH | `/agents/availability` | Update availability |

### Location

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/location` | Update GPS location |

### Dashboard & Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agent` | Agent dashboard |
| GET | `/agent/orders` | My assigned orders |
| GET | `/agent/orders/{id}` | Order details |
| PATCH | `/agent/orders/{id}/status` | Update status |
| POST | `/agent/orders/{id}/complete` | Complete delivery |

---

## Failed Deliveries

### Mark Failed (Agent)
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

### Request Reschedule (Customer)
```http
POST /failed-deliveries/{order_id}/reschedule
Authorization: Bearer <token>
Content-Type: application/json

{
  "preferred_date": "2024-01-15T10:00:00Z",
  "preferred_time_slot": "morning",
  "reason": "Was not home"
}
```

### Admin: Approve Reschedule
```http
PATCH /failed-deliveries/reschedule-requests/{id}/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "new_agent_id": "uuid..."
}
```

### Admin: Reject Reschedule
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

| Status | Description |
|--------|-------------|
| created | Order created, awaiting assignment |
| assigned | Agent assigned, awaiting pickup |
| picked_up | Package picked up by agent |
| in_transit | Package in transit to destination |
| out_for_delivery | Package out for final delivery |
| delivered | Successfully delivered |
| failed | Delivery attempt failed |
| cancelled | Order cancelled |

## Status Codes

| Code | Description |
|------|-------------|
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

## Pagination
- `skip`: Number of records to skip
- `limit`: Max records per page (max 100)

## Filtering
- `status`: Filter by order status
- `order_type`: Filter by order type (b2b/b2c)
- `payment_type`: Filter by payment type (prepaid/cod)