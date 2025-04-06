"""
Scheduler service for the VRM API client using APScheduler.
This service schedules and manages periodic data collection to InfluxDB.
"""
import logging
import time
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from vrm_client.services.influxdb_service import InfluxDBService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic data collection jobs."""

    def __init__(self,
                 influxdb_service: InfluxDBService,
                 collection_interval: int = 5,
                 max_workers: int = 10):
        """Initialize the scheduler service.

        Args:
            influxdb_service: InfluxDBService instance for data storage
            collection_interval: Data collection interval in seconds
            max_workers: Maximum number of worker threads
        """
        self.influxdb_service = influxdb_service
        self.collection_interval = collection_interval

        # Initialize scheduler
        executors = {
            "default": ThreadPoolExecutor(max_workers=max_workers)
        }

        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 15  # 15 seconds grace time for misfires
        }

        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC"
        )

        # Set up event listeners for job monitoring
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # Flags for controlling the service
        self.running = False
        self.job_ids = []

        logger.info(f"Scheduler service initialized with {collection_interval}s collection interval")

    def _job_listener(self, event):
        """Event listener for scheduler job events."""
        if hasattr(event, "exception") and event.exception:
            logger.error(f"Job {event.job_id} raised an exception: {event.exception}")
        else:
            if hasattr(event, "retval"):
                logger.debug(f"Job {event.job_id} executed successfully: {event.retval}")

    def collect_all_data(self) -> bool:
        """Collect data from all installations and write to InfluxDB.

        Returns:
            True if data collection was successful
        """
        logger.debug("Starting scheduled data collection for all installations")
        start_time = time.time()

        try:
            # Use the existing sync_live_data method from influxdb_service
            self.influxdb_service.sync_live_data()
            
            execution_time = time.time() - start_time
            logger.info(f"Data collection completed successfully, execution time: {execution_time:.2f}s")
            
            return True

        except Exception as e:
            logger.error(f"Error in scheduled data collection: {e}", exc_info=True)
            return False

    def start(self):
        """Start the scheduler service."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Schedule data collection job
            job = self.scheduler.add_job(
                self.collect_all_data,
                trigger=IntervalTrigger(seconds=self.collection_interval),
                id="all_installations_collector",
                name="Collect All Installations Data",
                replace_existing=True
            )
            self.job_ids.append(job.id)

            # Start the scheduler
            self.scheduler.start()
            self.running = True

            logger.info(
                f"Scheduler started with {self.collection_interval} second interval "
                f"for data collection"
            )

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)

    def add_custom_job(self, func: Callable, interval: int, job_id: str, name: str = None):
        """Add a custom scheduled job.

        Args:
            func: Function to execute
            interval: Interval in seconds
            job_id: Unique job identifier
            name: Human-readable name for the job
        """
        if not self.scheduler.running:
            self.scheduler.start()
            self.running = True

        job = self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=interval),
            id=job_id,
            name=name or job_id,
            replace_existing=True
        )
        self.job_ids.append(job.id)

        logger.info(f"Added custom job: {name or job_id} with {interval}s interval")
        return job

    def stop(self):
        """Stop the scheduler service."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return

        try:
            # Shutdown scheduler
            self.scheduler.shutdown(wait=False)
            self.running = False
            logger.info("Scheduler stopped")

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)

    def pause_job(self, job_id: str):
        """Pause a scheduled job.

        Args:
            job_id: ID of the job to pause
        """
        if job_id in self.job_ids:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")

    def resume_job(self, job_id: str):
        """Resume a paused job.

        Args:
            job_id: ID of the job to resume
        """
        if job_id in self.job_ids:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")

    def modify_interval(self, job_id: str, new_interval: int):
        """Modify the interval of a scheduled job.

        Args:
            job_id: ID of the job to modify
            new_interval: New interval in seconds
        """
        if job_id in self.job_ids:
            self.scheduler.reschedule_job(
                job_id,
                trigger=IntervalTrigger(seconds=new_interval)
            )
            logger.info(f"Modified job {job_id} interval to {new_interval}s")
