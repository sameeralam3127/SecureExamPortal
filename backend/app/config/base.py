from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SecureExamPortal API"
    app_version: str = "v1"
    environment: str = "development"
    auth_secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 720
    google_client_id: str = ""
    frontend_base_url: str = "http://localhost:5173"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@secureexamportal.com"
    smtp_use_tls: bool = True
    database_url: str = (
        "postgresql+psycopg://secure_exam_user:secure_exam_password@localhost:5432/"
        "secure_exam_portal"
    )
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
