# Event Tracking Specification (Product Analytics)

This spec defines **what to track**, **how to name events**, and **how to keep tracking stable** so downstream KPI reporting and A/B tests are reliable.

---

## Principles
1. **Stable names, stable meaning**  
When meaning changes, create a new event name and keep the old one for backwards compatibility.
2. **Consistent property keys**  
   Use snake_case. Prefer enums over free text.
3. **Event-level ownership**  
   Every event has an owner (PM / Analyst). Changes require approval + version note.
4. **One source of truth**  
   The spec is the contract. Dashboards and dbt models should reference the spec.

---

## Naming rules
**Format:** `noun_verb` or `object_action`, lower snake_case.

 Good:
- `signup_completed`
- `checkout_started`
- `purchase_completed`

 Bad:
- `SignupComplete` (mixed case)
- `purchase` (ambiguous)
- `clicked_button` (UI-specific and unstable)

---

## Required base properties (all events)
| Property | Type | Example | Notes |
|---|---:|---|---|
| `event_id` | uuid | `...` | Unique event id |
| `event_ts` | timestamp | `2026-02-24T12:34:56Z` | UTC |
| `user_id` | string | `u_001234` | Stable, not session-scoped |
| `session_id` | string | `s_00abcd` | New per app session |
| `platform` | enum | `web`, `ios`, `android` | Optional but recommended |
| `experiment_key` | string | `new_checkout` | Null if not part of experiment |
| `variant` | enum | `control`, `treatment` | Null if not part of experiment |

---

## Event catalog

### 1) app_open
Triggered when the user opens the app or lands on the site.

Properties:
- `referrer` (string, optional)
- `utm_source` (string, optional)
- `utm_campaign` (string, optional)

### 2) signup_started
Triggered when user begins signup flow.

Properties:
- `signup_method` (enum: `email`, `google`, `apple`)

### 3) signup_completed
Triggered when signup is fully completed (account created).

Properties:
- `signup_method` (enum)
- `country` (string, ISO2 preferred)

### 4) product_view
Triggered when a product detail page is viewed.

Properties:
- `product_id` (string)
- `category` (string, optional)
- `price` (numeric, optional)

### 5) add_to_cart
Triggered when a product is added to cart.

Properties:
- `product_id` (string)
- `quantity` (int)
- `price` (numeric)

### 6) checkout_started
Triggered when checkout is initiated.

Properties:
- `cart_value` (numeric)
- `items` (int)

### 7) purchase_completed
Triggered when payment succeeds and order is confirmed.

Properties:
- `order_id` (string)
- `revenue` (numeric)
- `currency` (string, ISO preferred)
- `items` (int)

---

## Bad vs good tracking examples

### Example: Checkout redesign experiment
**Bad tracking (unstable):**
- Event: `button_click`
- Property: `button_text = "Pay now"`
Why bad:
- UI labels change
- Meaning of “click” is not business outcome

**Good tracking (stable + measurable):**
- Event: `checkout_started`
- Event: `purchase_completed`
- Experiment: `experiment_key=new_checkout`, `variant=control|treatment`
Why good:
- Tied to business outcomes
- Works for funnels and A/B tests
- Minimal surface area for breaking changes

---

## Change control
- Any change must update this spec + include a short note:
  - what changed
  - why
  - date
  - owner

Downstream rule: if the KPI cannot be explained from this spec, instrumentation or definitions are incomplete.
