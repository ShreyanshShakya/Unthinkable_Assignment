# Database Schema Documentation

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │    Zone     │       │ ZoneArea    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ email       │       │ name        │       │ zone_id (FK)│
│ password    │       │ code        │       │ name        │
│ full_name   │       │ description │       │ pincode     │
│ phone       │       │ latitude    │       │ city        │
│ role        │       │ longitude   │       │ state       │
│ is_active   │       │ is_active   │       │ is_active   │
└──────┬──────┘       └──────┬──────┘       └─────────────┘
       │                     │
       │              ┌──────▼──────┐
       │              │  RateCard   │
       │              ├─────────────┤
       │              │ id (PK)     │
       │              │ name        │
       │              │ order_type  │
       │              │ zone_type   │
       │              │ is_active   │
       │              │ eff_from    │
       │              │ eff_to      │
       │              └──────┬──────┘
       │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌────────────────┐
│   Order     │      │RateCardRule │      │  CODSurcharge  │
├─────────────┤      ├─────────────┤      ├────────────────┤
│ id (PK)     │      │ id (PK)     │      │ id (PK)        │
│ order_num   │      │ rate_card_id│      │ rate_card_id   │
│ customer_id │      │ pickup_z_id │      │ min_order_val  │
│ agent_id    │      │ drop_z_id   │      │ max_order_val  │
│ pickup_addr │      │ min_weight  │      │ surcharge_pct  │
│ drop_addr   │      │ max_weight  │      │ min_surcharge  │
│ pickup_pin  │      │ base_charge │      │ max_surcharge  │
│ drop_pin    │      └─────────────┘      │ is_active      │
│ dimensions  │                           └────────────────┘
│ weights     │
│ order_type  │      ┌─────────────────┐
│ pay_type    │      │OrderStatusHist  │
│ zone_type   │      ├─────────────────┤
│ pricing     │      │ id (PK)         │
│ status      │      │ order_id (FK)   │
│ timestamps  │      │ old_status      │
└──────┬──────┘      │ new_status      │
       │             │ actor_id (FK)   │
       │             │ actor_role      │
       │             │ reason          │
┌──────▼──────┐      │ created_at      │
│   Agent     │      └─────────────────┘
├─────────────┤
│ id (PK)     │ ┌──────────────┐ ┌────────────────┐
│ user_id(FK) │ │AgentLocation │ │DeliveryAttempt │
│ employee_id │ ├──────────────┤ ├────────────────┤
│ zone_id(FK) │ │ id (PK)      │ │ id (PK)        │
│ status      │ │ agent_id(FK) │ │ order_id (FK)  │
│ max_deliv   │ │ latitude     │ │ agent_id (FK)  │
│ curr_deliv  │ │ longitude    │ │ attempt_num    │
└─────────────┘ │ accuracy     │ │ status         │
                │ zone_id(FK)  │ │ failure_reason │
                └──────────────┘ │ lat/long       │
                                 │ proof_of_deliv │
                                 │ timestamps     │
                                 └────────────────┘
```

## Tables

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR(255) | NOT NULL |
| full_name | VARCHAR(255) | NOT NULL |
| phone | VARCHAR(20) | |
| role | ENUM | NOT NULL (customer, agent, admin) |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Indexes**: email, (email, role)

### zones
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| code | VARCHAR(20) | UNIQUE, NOT NULL |
| description | TEXT | |
| latitude | NUMERIC(9,6) | NULL; zone center latitude |
| longitude | NUMERIC(9,6) | NULL; zone center longitude |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

Zone coordinates are an optional single center point used by the MVP assignment algorithm for distance ranking against the agent's latest GPS location.

### zone_areas
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| zone_id | UUID | FK → zones.id, NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| pincode | VARCHAR(10) | NOT NULL |
| city | VARCHAR(100) | |
| state | VARCHAR(100) | |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Constraints**: UNIQUE(zone_id, pincode)
**Indexes**: pincode, (pincode, city)

### rate_cards
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL |
| order_type | ENUM | NOT NULL (b2b, b2c) |
| zone_type | ENUM | NOT NULL (intra_zone, inter_zone) |
| is_active | BOOLEAN | DEFAULT true |
| effective_from | TIMESTAMP | DEFAULT now() |
| effective_to | TIMESTAMP | |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Constraints**: UNIQUE(name, order_type, zone_type)
**Indexes**: (order_type, zone_type, is_active)

### rate_card_rules
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| rate_card_id | UUID | FK → rate_cards.id, NOT NULL |
| pickup_zone_id | UUID | FK → zones.id, NOT NULL |
| drop_zone_id | UUID | FK → zones.id, NOT NULL |
| min_weight_kg | NUMERIC(10,3) | NOT NULL, ≥ 0 |
| max_weight_kg | NUMERIC(10,3) | NULL (unlimited if NULL) |
| base_charge | NUMERIC(10,2) | NOT NULL, ≥ 0 |
| per_kg_charge | NUMERIC(10,2) | DEFAULT 0, ≥ 0 |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Constraints**: min_weight_kg ≥ 0; max_weight_kg IS NULL OR max_weight_kg > min_weight_kg; base_charge ≥ 0; per_kg_charge ≥ 0.
**Indexes**: (rate_card_id, pickup_zone_id, drop_zone_id, min_weight_kg)

### cod_surcharges
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| rate_card_id | UUID | FK → rate_cards.id, NOT NULL |
| min_order_value | NUMERIC(10,2) | DEFAULT 0, ≥ 0 |
| max_order_value | NUMERIC(10,2) | NULL |
| surcharge_percentage | NUMERIC(5,2) | NOT NULL, 0-100 |
| min_surcharge | NUMERIC(10,2) | DEFAULT 0, ≥ 0 |
| max_surcharge | NUMERIC(10,2) | NULL |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Constraints**: surcharge_percentage 0-100; min_surcharge ≥ 0; max_surcharge ≥ min_surcharge; max_order_value > min_order_value.
**Indexes**: (rate_card_id, min_order_value, is_active)

### orders
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| order_number | VARCHAR(30) | UNIQUE, NOT NULL |
| customer_id | UUID | FK → users.id, NOT NULL |
| agent_id | UUID | FK → users.id, NULL |
| pickup_address | TEXT | NOT NULL |
| pickup_pincode | VARCHAR(10) | NOT NULL |
| pickup_city | VARCHAR(100) | |
| pickup_state | VARCHAR(100) | |
| pickup_zone_id | UUID | FK → zones.id, NULL |
| drop_address | TEXT | NOT NULL |
| drop_pincode | VARCHAR(10) | NOT NULL |
| drop_city | VARCHAR(100) | |
| drop_state | VARCHAR(100) | |
| drop_zone_id | UUID | FK → zones.id, NULL |
| length_cm | NUMERIC(10,2) | NOT NULL |
| breadth_cm | NUMERIC(10,2) | NOT NULL |
| height_cm | NUMERIC(10,2) | NOT NULL |
| actual_weight_kg | NUMERIC(10,3) | NOT NULL |
| volumetric_weight_kg | NUMERIC(10,3) | NOT NULL |
| billable_weight_kg | NUMERIC(10,3) | NOT NULL |
| order_type | ENUM | NOT NULL (b2b, b2c) |
| payment_type | ENUM | NOT NULL (prepaid, cod) |
| zone_type | ENUM | NOT NULL (intra_zone, inter_zone) |
| base_charge | NUMERIC(10,2) | NOT NULL |
| cod_surcharge | NUMERIC(10,2) | DEFAULT 0 |
| total_charge | NUMERIC(10,2) | NOT NULL |
| status | ENUM | DEFAULT 'created' |
| failure_reason | TEXT | |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |
| picked_up_at | TIMESTAMP | |
| delivered_at | TIMESTAMP | |

**Constraints**: actual_weight_kg > 0; billable_weight_kg ≥ actual_weight_kg; total_charge ≥ 0.
**Indexes**: (customer_id, status), (agent_id, status), (created_at, status)

### order_status_history
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| order_id | UUID | FK → orders.id, NOT NULL |
| old_status | ENUM | NULL (for initial) |
| new_status | ENUM | NOT NULL |
| actor_id | UUID | FK → users.id, NOT NULL |
| actor_role | ENUM | NOT NULL |
| reason | TEXT | |
| context_data | JSON | |
| created_at | TIMESTAMP | DEFAULT now() |

**Indexes**: (order_id, created_at)

### agents
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE, NOT NULL |
| employee_id | VARCHAR(50) | UNIQUE, NOT NULL |
| zone_id | UUID | FK → zones.id, NULL |
| status | ENUM | DEFAULT 'offline' |
| max_concurrent_deliveries | INTEGER | DEFAULT 3 |
| current_deliveries_count | INTEGER | DEFAULT 0 |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

### agent_locations
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| agent_id | UUID | FK → agents.id, UNIQUE, NOT NULL |
| latitude | NUMERIC(10,8) | NOT NULL |
| longitude | NUMERIC(11,8) | NOT NULL |
| accuracy_meters | INTEGER | |
| zone_id | UUID | FK → zones.id, NULL |
| updated_at | TIMESTAMP | DEFAULT now() |

### delivery_assignments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| order_id | UUID | FK → orders.id, UNIQUE, NOT NULL |
| agent_id | UUID | FK → agents.id, NOT NULL |
| assigned_by | UUID | FK → users.id, NULL |
| assigned_at | TIMESTAMP | DEFAULT now() |
| accepted_at | TIMESTAMP | |
| is_auto_assigned | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

### delivery_attempts
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| order_id | UUID | FK → orders.id, NOT NULL |
| agent_id | UUID | FK → agents.id, NOT NULL |
| attempt_number | INTEGER | NOT NULL |
| status | ENUM | DEFAULT 'pending' |
| failure_reason | TEXT | |
| latitude | NUMERIC(10,8) | |
| longitude | NUMERIC(11,8) | |
| proof_of_delivery | TEXT | |
| started_at | TIMESTAMP | |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Constraints**: UNIQUE(order_id, attempt_number)
**Indexes**: (order_id, agent_id)

### notifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| order_id | UUID | FK → orders.id, NULL |
| type | VARCHAR(50) | NOT NULL (email, sms) |
| subject | VARCHAR(255) | |
| message | TEXT | NOT NULL |
| status | VARCHAR(20) | DEFAULT 'pending' |
| external_id | VARCHAR(100) | |
| error_message | TEXT | |
| sent_at | TIMESTAMP | |
| created_at | TIMESTAMP | DEFAULT now() |

**Indexes**: (user_id, created_at), (order_id, type)

### reschedule_requests
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| order_id | UUID | FK → orders.id, NOT NULL |
| customer_id | UUID | FK → users.id, NOT NULL |
| preferred_date | TIMESTAMP | NOT NULL |
| preferred_time_slot | VARCHAR(50) | |
| reason | TEXT | |
| status | VARCHAR(20) | DEFAULT 'pending' |
| approved_by | UUID | FK → users.id, NULL |
| approved_at | TIMESTAMP | |
| new_delivery_attempt_id | UUID | FK → delivery_attempts.id, NULL |
| created_at | TIMESTAMP | DEFAULT now() |
| updated_at | TIMESTAMP | DEFAULT now() |

**Indexes**: (order_id, status)

## Enums

### userrole
- customer
- agent
- admin

### ordertype
- b2b
- b2c

### paymenttype
- prepaid
- cod

### orderstatus
- created
- assigned
- picked_up
- in_transit
- out_for_delivery
- delivered
- failed
- cancelled

### agentstatus
- available
- busy
- offline

### zonetype
- intra_zone
- inter_zone

### deliveryattemptstatus
- pending
- in_progress
- delivered
- failed

## Assignment Notes

- An order enters `assigned` when an agent is selected; assignment does not imply pickup.
- Auto-assignment considers agent activity/availability and capacity, then prefers pickup-zone affinity, shorter Haversine distance from the zone center, and lower current load.
- Zone latitude/longitude are optional MVP center coordinates. Agent GPS is stored separately in `agent_locations`.

## Naming Conventions
- Tables: snake_case, plural
- Columns: snake_case
- Primary keys: `id` (UUID)
- Foreign keys: `{table}_id`
- Indexes: `ix_{table}_{column(s)}`
- Unique constraints: `uq_{table}_{column(s)}`
- Check constraints: `ck_{table}_{condition}`
- Foreign keys: `fk_{table}_{referenced_table}`
