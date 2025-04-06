#!/usr/bin/env python3
"""
Run apscheduler jobs to collect data from the VRM API and send it to InfluxDB.
"""
import os
import sys
import logging
import signal
import time

from vrm_client.api_client import VRMApiClient
from vrm_client.services.site_service import SiteService
from vrm_client.services.influxdb_service import InfluxDBService
from vrm_client.services.scheduler_service import SchedulerService


# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("vrm_client")

# Global flags and objects
scheduler_service = None
running = True


def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global running, scheduler_service
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    running = False

    if scheduler_service and scheduler_service.running:
        scheduler_service.stop()


def validate_environment():
    """Validate required environment variables."""
    missing_vars = []
    # Check InfluxDB variables
    influxdb_vars = ["INFLUXDB_URL", "INFLUXDB_TOKEN", "INFLUXDB_ORG", "INFLUXDB_BUCKET"]
    for var in influxdb_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file or Docker environment")
        sys.exit(1)

    return True


def main():
    """Main entrypoint function."""
    global scheduler_service

    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Validate environment
        validate_environment()

        # Get collection interval (default 5 seconds)
        collection_interval = int(os.getenv("DATA_COLLECTION_INTERVAL", 5))

        # Initialize API client
        logger.info("Initializing VRM API client")
        vrm_client = VRMApiClient()

        # Initialize services
        site_service = SiteService(vrm_client)

        influxdb_service = InfluxDBService(
            site_service,
            os.getenv("INFLUXDB_URL"),
            os.getenv("INFLUXDB_TOKEN"),
            os.getenv("INFLUXDB_ORG"),
            os.getenv("INFLUXDB_BUCKET"),
        )

        # Initialize scheduler service
        logger.info(f"Initializing scheduler with {collection_interval}s interval")
        scheduler_service = SchedulerService(
            influxdb_service,
            collection_interval=collection_interval
        )

        # Start the scheduler
        scheduler_service.start()

        # Print installation info
        installations = site_service.api.installations()
        logger.info(f"Monitoring {len(installations)} installations:")
        for installation in installations:
            logger.info(f"  - {installation.name} (ID: {installation.id})")

        # Keep the container running
        logger.info("VRM data collection service is running. Press Ctrl+C to stop.")
        while running:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure cleanup on exit
        if scheduler_service and scheduler_service.running:
            scheduler_service.stop()
        logger.info("Service shutdown complete")


if __name__ == "__main__":
    main()
