from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from vrm_client.api_client import VRMApiClient
from vrm_client.models import Installation, EnergyData, BatteryData

logger = logging.getLogger(__name__)


def _get_latest_timestamp(records: dict) -> int:
    # Collect timestamps from all data series and return the latest one
    timestamps = [
        series[-1][0] for series in records.values()
        if isinstance(series, list) and series
    ]
    return max(timestamps) if timestamps else int(datetime.now().timestamp() * 1000)


def _get_latest_value(values_array: list) -> Optional[float]:
    if values_array and len(values_array) > 0:
        # Return the most recent value (the last record, second element)
        return float(values_array[-1][1])
    return None


def _parse_stats(installation: Installation, data: dict) -> Optional[EnergyData]:
    records = data.get("records", {})

    latest_timestamp = _get_latest_timestamp(records)

    return EnergyData(
        installation=installation,
        timestamp=datetime.fromtimestamp(latest_timestamp / 1000),
        consumption=_get_latest_value(records.get("consumption")),
        ac_load=_get_latest_value(records.get("ac_loads")),
        grid=_get_latest_value(records.get("from_to_grid")),
        solar=_get_latest_value(records.get("solar_yield")),
        battery=BatteryData(
            timestamp=datetime.fromtimestamp(latest_timestamp / 1000),
            soc=_get_latest_value(records.get("bs")),
            voltage=_get_latest_value(records.get("bv"))
        )
    )


class SiteService:
    """Service for managing site/installation related operations."""

    def __init__(self, api_client: VRMApiClient):
        """Initialize with an API client instance.

        Args:
            api_client: Initialized VRMApiClient instance
        """
        self.api = api_client


    def _installation_data(self, installation: Installation) -> Dict[str, str]:
        start_time = int((datetime.now() - timedelta(minutes=5)).timestamp())
        params = {
            "start": start_time,
            "type": "custom",
            "attributeCodes[0]": "ac_loads",
            "attributeCodes[1]": "from_to_grid",
            "attributeCodes[2]": "consumption",
            "attributeCodes[3]": "solar_yield",
            "attributeCodes[4]": "bs",
            "attributeCodes[5]": "bv",
        }

        response = self.api._make_request("GET", f"installations/{installation.id}/stats", params=params)
        return response


    def data(self) -> Optional[List[EnergyData]]:
        """Fetch live data for all installations.
        Returns:
            List of EnergyData objects for each installation
        """
        data = []
        for installation in self.api.installations():
            stats = self._installation_data(installation)
            energy_data = _parse_stats(installation, stats)
            data.append(energy_data)

        return data
