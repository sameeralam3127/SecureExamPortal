import logging
import os

from app.services.job_queue import run_worker


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


if __name__ == "__main__":
    poll_interval = float(os.getenv("WORKER_POLL_INTERVAL_SECONDS", "2"))
    run_worker(poll_interval=poll_interval)
