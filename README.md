# Expense Tracker Backend (Django)

REST API for an expense tracker — JWT auth, categories, income/expense transactions, budgets, and reports. Frontend is separate; give your friend [API.md](API.md).

## Quick start (local)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
python manage.py migrate
python manage.py runserver
```

API base: `http://127.0.0.1:8000/api/`

- Swagger UI: http://127.0.0.1:8000/api/docs/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

## Main endpoints

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/auth/register/` | No |
| POST | `/api/auth/login/` | No |
| POST | `/api/auth/refresh/` | No |
| GET | `/api/auth/me/` | JWT |
| CRUD | `/api/categories/` | JWT |
| CRUD | `/api/transactions/` | JWT |
| CRUD | `/api/budgets/` | JWT |
| GET | `/api/reports/summary/` | JWT |
| GET | `/api/reports/monthly/` | JWT |

Full request/response examples: **[API.md](API.md)**

## Environment variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret (required in production) |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `DATABASE_URL` | Postgres URL on Render; omit locally for SQLite |
| `SECURE_SSL_REDIRECT` | Default `True` when `DEBUG=False` |

## Deploy on Render

1. Push this repo to GitHub.
2. On [Render](https://render.com): **New → Blueprint** and select the repo (uses `render.yaml`), **or** create manually:
   - **PostgreSQL** database
   - **Web Service** (Python)
     - Build: `./build.sh` (or `chmod +x build.sh && ./build.sh`)
     - Start: `gunicorn expense_tracker.wsgi:application`
3. Set env vars:
   - `SECRET_KEY` (generate random)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-service.onrender.com`
   - `DATABASE_URL` (from the Render Postgres service)
   - `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com`
4. Deploy. Share the public URL + [API.md](API.md) with your frontend friend.

### Windows note for `build.sh`

Render runs Linux. Locally on Windows you do not need `build.sh`; use `migrate` + `runserver` as above.

## Admin (optional)

```bash
python manage.py createsuperuser
```

Then open http://127.0.0.1:8000/admin/
