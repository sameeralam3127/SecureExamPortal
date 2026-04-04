from app.config.base import Settings


class TestingSettings(Settings):
    environment: str = "testing"
