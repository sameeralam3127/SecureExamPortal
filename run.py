# run.py
import logging
import os
from logging.handlers import RotatingFileHandler

from app import create_app, db


def main():
    app = create_app()

    # Setup logging
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=10)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("App startup")
    

    # Try multiple ports if busy
    port = 5000
    while True:
        try:
            app.run(debug=True, host="0.0.0.0", port=port)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} busy, trying next port...")
                port += 1
            else:
                raise


if __name__ == "__main__":
    main()
