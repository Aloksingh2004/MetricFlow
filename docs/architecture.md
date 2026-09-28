# V1 architecture

```text
CSV/XLSX -> FastAPI upload -> pandas validation/cleaning -> SQLAlchemy orders table
     -> KPI service -> Streamlit dashboard / Excel report -> saved schedule
```

The backend is a modular monolith. This keeps ingestion, KPI calculation, reporting, and scheduling in one deployable service for the first customer cohort. The persistence layer uses SQLAlchemy so local SQLite can be switched to PostgreSQL through `DATABASE_URL` without changing application code.

Data semantics: an order is revenue-eligible only when its normalized status is `completed`. Refund rate is refunded records divided by all records in the selected range. Top products rank successful records by `quantity × unit_price`.
