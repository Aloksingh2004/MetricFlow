from sqlalchemy import inspect, text

from app.db.base import engine


TENANT_TABLES = ("orders", "uploads", "reports", "schedules")


def ensure_tenant_columns() -> None:
    """Keep development databases compatible with user-scoped V1 records.

    Production deployments should run a reviewed migration before release. This
    compatibility step never assigns legacy records to a user, so they remain
    inaccessible until intentionally migrated by an administrator.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name in TENANT_TABLES:
            if table_name not in existing_tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table_name)}
            if "user_id" not in columns:
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN user_id VARCHAR(36)"))
