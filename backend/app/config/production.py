from app.config.base import Settings


class ProductionSettings(Settings):
    environment: str = "production"
