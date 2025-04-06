"""
Service for transferring VRM data to InfluxDB Cloud.
"""
import logging
from typing import Optional

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from vrm_client.services.site_service import SiteService
from vrm_client.models import EnergyData

from vrm_client.config import (
    INFLUXDB_URL,
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET
)

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Service for transferring VRM data to InfluxDB Cloud."""

    def __init__(self,
                 site_service: SiteService,
                 influx_url: Optional[str] = None,
                 influx_token: Optional[str] = None,
                 influx_org: Optional[str] = None,
                 influx_bucket: Optional[str] = None,
                 ):
        """Initialize with API client and InfluxDB connection parameters.

        Args:
            site_service: SiteService instance
            influx_url: InfluxDB Cloud URL
            influx_token: InfluxDB Cloud API token
            influx_org: InfluxDB organization
            influx_bucket: InfluxDB bucket name
        """
        self.site_service = site_service

        # Initialize InfluxDB client
        self.influx_client = InfluxDBClient(
            url=influx_url or INFLUXDB_URL,
            token=influx_token or INFLUXDB_TOKEN,
            org=influx_org or INFLUXDB_ORG,
        )
        self.bucket = influx_bucket or INFLUXDB_BUCKET
        self.org = influx_org or INFLUXDB_ORG

        logger.info(f"InfluxDB service initialized for bucket: {influx_bucket}")


    def _create_data_point(self, energy_data: EnergyData) -> Point:
        """Create a data point for InfluxDB from EnergyData."""

        point = Point("fve_data").tag("site", energy_data.name).tag("installation_id", energy_data.installation_id)
        point.field("consumption", energy_data.consumption)
        point.field("ac_load", energy_data.ac_load)
        point.field("grid", energy_data.grid)
        point.field("solar", energy_data.solar)
        point.field("battery_soc", energy_data.battery.soc)
        point.field("battery_voltage", energy_data.battery.voltage)

        logger.debug(f"Point created successfully: {point}")
        return point

    def sync_live_data(self):
        write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        data = self.site_service.data()
        points = []
        for energy_data in data:
            points.append(self._create_data_point(energy_data))

        points.append(self._create_sum_of_data_points(points))
        write_api.write(bucket=self.bucket, org=self.org, record=points, precision="s")

    def _create_sum_of_data_points(self, points: [Point]) -> Point:
        """
            Create a summary point for InfluxDB from multiple data points.
            Summarize all FVE into one point.
        """

        overview_point = Point("solar_system")
        field_sums = {}
        for point in points:
            for field_key, field_value in point._fields.items():

                if field_key in field_sums:
                    field_sums[field_key] += field_value or 0.0
                else:
                    field_sums[field_key] = field_value or 0.0

        for field_key, field_sum in field_sums.items():
            overview_point.field(field_key, field_sum)

        return overview_point

    def close(self):
        """Close the InfluxDB client connection."""
        self.influx_client.close()
