# Expense Tracker API — Frontend Guide

Give this file to whoever builds the frontend.

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local | `http://127.0.0.1:8000/api` |
| Production (Render) | `https://YOUR-APP.onrender.com/api` |

Interactive docs (after server is running): `GET /api/docs/`

---

## Authentication

All endpoints except **register**, **login**, and **refresh** require:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

| Token | Lifetime |
|-------|----------|
| `access` | 1 hour |
| `refresh` | 7 days |

**Frontend checklist**

1. Call register or login → store `access` and `refresh` (memory / localStorage / secure cookie).
2. Send `Authorization: Bearer <access>` on every protected request.
3. On `401`, call refresh with the refresh token → save new `access` → retry.
4. If refresh fails, redirect to login.

---

## Auth endpoints

### Register — `POST /api/auth/register/`

Creates the user, seeds default categories, returns tokens.

**Request**

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

**Response `201`**

```json
{
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "date_joined": "2026-09-24T12:00:00+05:30"
  },
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

**Errors:** `400` validation (duplicate username/email, weak password, mismatch).

---

### Login — `POST /api/auth/login/`

**Request**

```json
{
  "username": "alice",
  "password": "StrongPass123!"
}
```

**Response `200`**

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>"
}
```

**Errors:** `401` invalid credentials.

---

### Refresh — `POST /api/auth/refresh/`

**Request**

```json
{
  "refresh": "<refresh_jwt>"
}
```

**Response `200`**

```json
{
  "access": "<new_access_jwt>"
}
```

---

### Current user — `GET /api/auth/me/`

**Headers:** Bearer token required.

**Response `200`**

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "date_joined": "2026-09-24T12:00:00+05:30"
}
```

---

## Categories

Default categories are created on register (Food, Transport, Shopping, Bills, Entertainment, Health, Salary, Freelance, Other).

### List — `GET /api/categories/`

Query params:

| Param | Description |
|-------|-------------|
| `type` | `income` or `expense` |
| `search` | Filter by name |
| `page` | Page number (page size 20) |
| `ordering` | `name`, `type`, `created_at` (prefix `-` for desc) |

**Response `200`** (paginated)

```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Food",
      "type": "expense",
      "color": "#EF4444",
      "created_at": "2026-09-24T12:00:00+05:30"
    }
  ]
}
```

### Create — `POST /api/categories/`

```json
{
  "name": "Rent",
  "type": "expense",
  "color": "#A855F7"
}
```

### Retrieve / Update / Delete

- `GET /api/categories/{id}/`
- `PUT /api/categories/{id}/` (full) / `PATCH /api/categories/{id}/` (partial)
- `DELETE /api/categories/{id}/` → `204`

Users only see/edit their own categories.

---

## Transactions (income & expense)

### List — `GET /api/transactions/`

| Param | Description |
|-------|-------------|
| `type` | `income` or `expense` |
| `category` | Category ID |
| `start` | `YYYY-MM-DD` (inclusive) |
| `end` | `YYYY-MM-DD` (inclusive) |
| `search` | Search in `note` |
| `page` | Pagination |
| `ordering` | `date`, `amount`, `created_at` |

**Response item**

```json
{
  "id": 5,
  "category": 1,
  "category_name": "Food",
  "type": "expense",
  "amount": "250.00",
  "date": "2026-09-20",
  "note": "Lunch",
  "created_at": "2026-09-20T14:00:00+05:30",
  "updated_at": "2026-09-20T14:00:00+05:30"
}
```

### Create — `POST /api/transactions/`

```json
{
  "category": 1,
  "type": "expense",
  "amount": "250.00",
  "date": "2026-09-20",
  "note": "Lunch"
}
```

**Rules**

- `amount` must be `> 0`
- `category` must belong to the logged-in user
- `category.type` must equal `type` (`income` / `expense`)

### Retrieve / Update / Delete

- `GET /api/transactions/{id}/`
- `PUT` / `PATCH /api/transactions/{id}/`
- `DELETE /api/transactions/{id}/` → `204`

---

## Budgets (expense categories only)

### List — `GET /api/budgets/`

| Param | Description |
|-------|-------------|
| `month` | `1`–`12` |
| `year` | e.g. `2026` |
| `page` | Pagination |

**Response item**

```json
{
  "id": 1,
  "category": 1,
  "category_name": "Food",
  "month": 9,
  "year": 2026,
  "limit_amount": "5000.00",
  "spent": "1250.00",
  "remaining": "3750.00",
  "created_at": "...",
  "updated_at": "..."
}
```

`spent` / `remaining` are computed from expense transactions in that month.

### Create — `POST /api/budgets/`

```json
{
  "category": 1,
  "month": 9,
  "year": 2026,
  "limit_amount": "5000.00"
}
```

One budget per user + category + month + year.

### Retrieve / Update / Delete

- `GET /api/budgets/{id}/`
- `PUT` / `PATCH /api/budgets/{id}/`
- `DELETE /api/budgets/{id}/` → `204`

---

## Reports

### Summary — `GET /api/reports/summary/`

| Param | Default |
|-------|---------|
| `month` | Current month |
| `year` | Current year |

**Response `200`**

```json
{
  "month": 9,
  "year": 2026,
  "total_income": "50000.00",
  "total_expense": "18250.00",
  "balance": "31750.00",
  "by_category": [
    {
      "category_id": 1,
      "category_name": "Food",
      "type": "expense",
      "total": "3200.00"
    },
    {
      "category_id": 8,
      "category_name": "Salary",
      "type": "income",
      "total": "50000.00"
    }
  ],
  "budgets": [
    {
      "budget_id": 1,
      "category_id": 1,
      "category_name": "Food",
      "limit_amount": "5000.00",
      "spent": "3200.00",
      "remaining": "1800.00",
      "over_budget": false
    }
  ]
}
```

Use for dashboard totals, pie charts (`by_category`), and budget warnings (`over_budget`).

---

### Monthly trend — `GET /api/reports/monthly/`

| Param | Default | Max |
|-------|---------|-----|
| `months` | `6` | `24` |

**Response `200`**

```json
{
  "months": 6,
  "series": [
    {
      "year": 2026,
      "month": 4,
      "label": "2026-04",
      "income": "48000.00",
      "expense": "21000.00",
      "balance": "27000.00"
    }
  ]
}
```

Use for line/bar charts over time.

---

## Pagination shape

List endpoints return:

```json
{
  "count": 42,
  "next": "http://.../api/transactions/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## Common HTTP status codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | Deleted (no body) |
| 400 | Validation error |
| 401 | Missing/invalid/expired token |
| 403 | Forbidden |
| 404 | Not found (or not yours) |

Validation error example:

```json
{
  "amount": ["Ensure this value is greater than or equal to 0.01."],
  "category": ["Category type 'income' does not match transaction type 'expense'."]
}
```

---

## CORS

Backend allows origins listed in `CORS_ALLOWED_ORIGINS`. For local Vite/React, typically:

```text
http://localhost:3000
http://localhost:5173
```

Ask the backend owner to add your production frontend URL on Render.

---

## Suggested frontend screens

1. **Login / Register**
2. **Dashboard** — `reports/summary` + `reports/monthly`
3. **Transactions** — list + filters + create/edit form
4. **Categories** — manage custom categories
5. **Budgets** — set monthly limits; show spent vs remaining

Amounts are decimal strings (e.g. `"250.00"`) — good for money; do not use JS floats for money math if possible.
