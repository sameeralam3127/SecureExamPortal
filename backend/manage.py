import uvicorn

from app.config.base import get_settings
from app.extensions.db import init_db


def main() -> None:
    settings = get_settings()
    init_db()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
