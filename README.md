# MetricFlow

MetricFlow is a focused reporting automation SaaS for D2C and e-commerce businesses. It accepts sales exports, validates and cleans them, stores orders, calculates sales KPIs, generates an Excel report, and saves recurring report schedules.

## What is included

- FastAPI backend with OpenAPI documentation at `http://localhost:8000/docs`
- Streamlit frontend with Login, Dashboard, Data Upload, Reports, and Automation screens
- CSV/XLS/XLSX support; validation for required fields, types, statuses, missing values, and duplicate order IDs
- KPI calculations: revenue, valid orders, average order value, refund rate, status breakdown, top products, and period-over-period revenue change
- SQLite for zero-setup local use; PostgreSQL configuration supplied for deployment
- Argon2 password hashing, short-lived signed JWTs, rate-limited login, and user-scoped data access

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r frontend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

In a second terminal:

```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

Open `http://localhost:8501` and sign in with `demo@metricflow.app` / `demo123`. Upload `data/sample_orders.csv` to see the dashboard populated.

## Configuration

Copy `.env.example` to `.env` and replace `SECRET_KEY` with a random 32+ character value. The default `DATABASE_URL=sqlite:///./metricflow.db` gives a fast local setup. For PostgreSQL, start the database and set:

```bash
docker compose up -d db
DATABASE_URL=postgresql+psycopg://metricflow:metricflow@localhost:5432/metricflow
```

Install the PostgreSQL driver with `pip install psycopg[binary]` when using that connection string.

## Import contract

Required fields are `order_id`, `order_date`, `product_name`, `quantity`, `unit_price`, and `status`. Optional fields are `customer_id`, `product_id`, and `payment_method`. Header names are normalized to lowercase snake case. Successful statuses include `paid`, `completed`, `fulfilled`, and `shipped`; `cancelled` and `refunded` are normalized as well.

Each imported order ID is unique across uploads. Re-uploading a file safely skips existing orders.

## Security

Every API route that accesses business data requires an `Authorization: Bearer <JWT>` header. Tokens expire after 30 minutes by default and are signed with `SECRET_KEY`; set a unique secret and `APP_ENV=production` in deployed environments. Records and generated files are scoped to the authenticated user, so an ID from another account returns `404` rather than exposing data.

Login passwords are stored with Argon2 hashes and login attempts are limited to five per IP/email pair every 15 minutes. The built-in demo account is created only outside production. For a production deployment, create user accounts through an admin/onboarding flow, configure exact `ALLOWED_ORIGINS` and `ALLOWED_HOSTS`, terminate TLS at the load balancer, and run an explicit reviewed database migration for existing data.

To bootstrap the first production account without exposing a public registration endpoint, run:

```bash
PYTHONPATH=backend python backend/scripts/create_user.py --email owner@yourcompany.com --role owner
```

## Delivery note

The API persists schedules and includes an APScheduler worker hook in `backend/app/services/scheduler.py`. Email delivery is intentionally deferred, per V1 scope; a deployed worker can load saved schedules and call the existing report generator.

## Tests

```bash
PYTHONPATH=backend pytest backend/tests
```
