from app.config.base import Settings


class DevelopmentSettings(Settings):
    environment: str = "development"
