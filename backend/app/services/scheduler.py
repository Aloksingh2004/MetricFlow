"""APScheduler hook for production worker deployment.

Schedules are persisted in the database by the API. A dedicated worker can load
active schedules from that table and register report-generation jobs here.
"""

from apscheduler.schedulers.background import BackgroundScheduler


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    return scheduler

