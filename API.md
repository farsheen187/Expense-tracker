# Expense Tracker API — Frontend Guide (PUBLIC)

**NO AUTHENTICATION REQUIRED**  
**NO JWT TOKEN REQUIRED**  
**NO AUTHORIZATION HEADER REQUIRED**

Use these APIs directly from the frontend.

## Base URL

| Environment | Base URL |
|-------------|----------|
| Local | `http://127.0.0.1:8000/api` |
| Production (Render) | `https://YOUR-APP.onrender.com/api` |

Swagger: `GET /api/docs/`

Required header for JSON writes:

```http
Content-Type: application/json
```

---

## Categories

### List — `GET /api/categories/`

Query: `type=income|expense`, `search`, `page`, `ordering`

### Create — `POST /api/categories/`

```json
{ "name": "Rent", "type": "expense", "color": "#A855F7" }
```

### Detail — `GET|PUT|PATCH|DELETE /api/categories/{id}/`

Default categories are seeded automatically (Food, Transport, Shopping, Bills, Entertainment, Health, Salary, Freelance, Other).

---

## Transactions

### List — `GET /api/transactions/`

Query: `type`, `category`, `start`, `end`, `search`, `page`, `ordering`

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

### Detail — `GET|PUT|PATCH|DELETE /api/transactions/{id}/`

---

## Budgets

### List — `GET /api/budgets/?month=9&year=2026`

### Create — `POST /api/budgets/`

```json
{
  "category": 1,
  "month": 9,
  "year": 2026,
  "limit_amount": "5000.00"
}
```

### Detail — `GET|PUT|PATCH|DELETE /api/budgets/{id}/`

---

## Reports

### Summary — `GET /api/reports/summary/?month=9&year=2026`

Returns `total_income`, `total_expense`, `balance`, `by_category`, `budgets`.

### Monthly — `GET /api/reports/monthly/?months=6`

Returns chart series for the last N months.

---

## Auth endpoints (optional / unused by frontend)

These still exist but are **not required**:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/` (requires JWT if used)

---

## Notes for frontend

1. Call APIs with no `Authorization` header.
2. Amounts are decimal strings (`"250.00"`).
3. Free Render services may sleep after idle; first request can take 30–60s.
4. CORS allows all origins in this deployment.
