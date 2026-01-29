"""
Background worker entry point for reporting-service event consumer.

Run this module directly to start consuming contract events:
    python -m src.worker
"""

import logging
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the event consumer worker."""
    from .event_consumer import start_event_consumer_worker

    # Database setup
    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://reporting_user:reporting_pass@localhost:3315/reporting_db",
    )

    logger.info(f"Connecting to database...")
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db_session():
        return SessionLocal()

    logger.info("Starting reporting event consumer worker...")
    start_event_consumer_worker(get_db_session)


if __name__ == "__main__":
    main()
