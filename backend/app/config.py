from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./metricflow.db"
    app_env: str = "development"
    secret_key: str = "development-only-secret-change-before-production"
    demo_email: str = "demo@metricflow.app"
    demo_password: str = "demo123"
    upload_dir: Path = Path("data/uploads")
    report_dir: Path = Path("data/reports")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    allowed_origins: list[str] = ["http://localhost:8501"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @field_validator("allowed_origins", "allowed_hosts", mode="before")
    @classmethod
    def split_csv_settings(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def block_development_secret_in_production(self):
        unsafe_prefixes = ("development-only-", "replace-this-")
        if self.app_env.lower() == "production" and self.secret_key.startswith(unsafe_prefixes):
            raise ValueError("Set a unique SECRET_KEY before starting in production")
        return self


settings = Settings()
