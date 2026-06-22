from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SecureExamPortal API"
    app_version: str = "v1"
    environment: str = "development"
    auth_secret_key: str = "local-development-secret"
    access_token_expire_minutes: int = 720
    auth_token_issuer: str = "secure-exam-portal"
    auth_token_audience: str = "secure-exam-portal-web"
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 60
    google_client_id: str = ""
    google_allowed_domains: list[str] = []
    frontend_base_url: str = "http://localhost:5173"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@secureexamportal.com"
    smtp_use_tls: bool = True
    database_url: str = (
        "postgresql+psycopg://secure_exam_user:local_dev_password@localhost:5432/"
        "secure_exam_portal"
    )
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    initial_admin_username: str = ""
    initial_admin_password: str = ""
    initial_admin_email: str = ""
    initial_admin_full_name: str = "Portal Administrator"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment.lower() != "production":
            return self

        if self.auth_secret_key == "local-development-secret":
            raise ValueError("AUTH_SECRET_KEY must be set for production")
        if len(self.auth_secret_key) < 32:
            raise ValueError("AUTH_SECRET_KEY must be at least 32 characters in production")
        if self.access_token_expire_minutes > 240:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be 240 or lower in production")
        if self.auth_rate_limit_attempts < 1:
            raise ValueError("AUTH_RATE_LIMIT_ATTEMPTS must be greater than zero")
        if self.auth_rate_limit_window_seconds < 1:
            raise ValueError("AUTH_RATE_LIMIT_WINDOW_SECONDS must be greater than zero")
        if "local_dev_password" in self.database_url:
            raise ValueError("DATABASE_URL must not use the local development database password")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins):
            raise ValueError("CORS_ORIGINS must contain production origins only")
        if not self.frontend_base_url.startswith("https://"):
            raise ValueError("FRONTEND_BASE_URL must use HTTPS in production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
