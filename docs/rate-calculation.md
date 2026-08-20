# Rate Calculation Explanation

## Overview
The pricing engine calculates delivery charges based on package dimensions, weight, zone configuration, order type, and payment method. All calculations happen server-side to prevent tampering.

## Calculation Formula

### 1. Volumetric Weight
```
Volumetric Weight (kg) = Length(cm) × Breadth(cm) × Height(cm) / 5000
```

**Example**: 30cm × 20cm × 15cm = 9000 cm³ → 9000 / 5000 = **1.8 kg**

### 2. Billable Weight
```
Billable Weight (kg) = max(Actual Weight, Volumetric Weight)
```

**Example**: Actual = 1.2 kg, Volumetric = 1.8 kg → Billable = **1.8 kg**

### 3. Zone Type Detection
- **Intra-zone**: Pickup zone = Drop zone
- **Inter-zone**: Pickup zone ≠ Drop zone

Zone detection uses pincode mapping from the `zone_areas` table with exact match first, then prefix fallback.

### 4. Rate Card Selection
Rate cards are filtered by:
1. **Order Type**: B2B or B2C
2. **Zone Type**: Intra-zone or Inter-zone
3. **Active Status**: Only active rate cards
4. **Effective Dates**: Within effective_from/to range

### 5. Rate Rule Matching
For the selected rate card, find the rule where:
- `pickup_zone_id` = order pickup zone
- `drop_zone_id` = order drop zone
- `min_weight_kg` ≤ billable_weight
- `max_weight_kg` ≥ billable_weight (or NULL for unlimited)

Rules ordered by `min_weight_kg` DESC for best match.

### 6. Base Charge Calculation
```
Additional Weight = max(0, Billable Weight - min_weight_kg)
Base Charge = base_charge + (Additional Weight × per_kg_charge)
```

**Example**: 
- Rule: min=5kg, max=10kg, base=₹100, per_kg=₹10
- Billable: 7.5 kg
- Additional = 7.5 - 5 = 2.5 kg
- Base = 100 + (2.5 × 10) = **₹125**

### 7. COD Surcharge
Applied only for `payment_type = COD`:

1. Find active surcharge where:
   - `min_order_value` ≤ order_value
   - `max_order_value` ≥ order_value (or NULL)
2. Calculate:
   ```
   Surcharge = (Order Value × surcharge_percentage) / 100
   Surcharge = max(Surcharge, min_surcharge)
   Surcharge = min(Surcharge, max_surcharge) if max_surcharge set
   ```

**Example**:
- Order value: ₹5000
- Surcharge: 2%, min ₹20, max ₹100
- Raw = 5000 × 0.02 = ₹100
- Capped at max = **₹100**

### 8. Total Charge
```
Total Charge = Base Charge + COD Surcharge
```

## Complete Example

**Order Details**:
- Dimensions: 40×30×20 cm
- Actual Weight: 2.5 kg
- Pickup: Delhi (Zone A) - pincode 110001
- Drop: Mumbai (Zone B) - pincode 400001
- Order Type: B2C
- Payment: COD
- Order Value: ₹3000

**Calculation**:
1. Volumetric = 40×30×20 / 5000 = **4.8 kg**
2. Billable = max(2.5, 4.8) = **4.8 kg**
3. Zone Type: Inter-zone (Zone A ≠ Zone B)
4. Rate Card: B2C + Inter-zone (active)
5. Rule Match: Zone A → Zone B, 0-5kg slab
   - Base: ₹80, per_kg: ₹15
6. Additional Weight = 4.8 - 0 = 4.8 kg
   Base = 80 + (4.8 × 15) = **₹152**
7. COD Surcharge: 3% min ₹25 max ₹100
   Raw = 3000 × 0.03 = ₹90 (within limits)
   Surcharge = **₹90**
8. **Total = ₹152 + ₹90 = ₹242**

## Price Stability
- Pricing snapshot stored on order creation
- Rate card changes don't affect existing orders
- Historical pricing preserved for audits

## API Endpoints
- `POST /api/pricing/calculate` - Calculate with zone IDs
- `POST /api/pricing/quote` - Quote with pincode auto-detection
- `GET /api/pricing/rate-cards/active` - List active rate cards

## Configuration
Admin can manage via `/admin/rates`:
- Create rate cards (B2B/B2C × Intra/Inter)
- Define weight slabs with base + per_kg charges
- Configure COD surcharges per rate card
- Set effective dates for future changes