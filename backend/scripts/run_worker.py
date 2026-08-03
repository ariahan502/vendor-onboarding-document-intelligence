"""Local polling worker for queued vendor packet processing.

Use `--once` for development or let it poll continuously in Docker. The worker uses
the same processing service as the API, keeping extraction and validation behavior
identical across local and containerized runs.
"""

import argparse
import time

from app.db.session import SessionLocal
from app.config import settings
from app.services.package_service import process_next_queued_package


def process_once() -> bool:
    db = SessionLocal()
    try:
        result = process_next_queued_package(db)
        if result is None:
            return False
        print(
            f"Processed {result.package_id}: {result.package_status} "
            f"with {result.finding_count} findings."
        )
        return True
    finally:
        db.close()


def main() -> None:
    settings.validate_production_configuration()
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Process at most one packet.")
    parser.add_argument("--poll-seconds", type=int, default=3)
    args = parser.parse_args()

    if args.once:
        if not process_once():
            print("No packets are queued for processing.")
        return

    while True:
        if not process_once():
            time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
