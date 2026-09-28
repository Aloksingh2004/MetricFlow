from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./metricflow.db"
    secret_key: str = "change-this-in-production"
    demo_email: str = "demo@metricflow.app"
    demo_password: str = "demo123"
    upload_dir: Path = Path("data/uploads")
    report_dir: Path = Path("data/reports")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

