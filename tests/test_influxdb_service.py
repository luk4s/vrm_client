import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from vrm_client.services.influxdb_service import InfluxDBService
from vrm_client.models import EnergyData, BatteryData


class TestInfluxDBService:
    """Tests for the InfluxDBService class."""

    @pytest.fixture
    def api_client_mock(self):
        """Create a mock API client."""
        return MagicMock()

    @pytest.fixture
    def site_service_mock(self, api_client_mock):
        """Create a mock SiteService."""
        return MagicMock(api=api_client_mock)

    @pytest.fixture
    def influxdb_client_mock(self):
        """Create a mock InfluxDB client."""
        mock = MagicMock()
        mock.write_api.return_value = MagicMock()
        return mock

    @pytest.fixture
    def influxdb_service(self, site_service_mock, influxdb_client_mock):
        """Create an InfluxDBService with mocked dependencies."""
        with patch('vrm_client.services.influxdb_service.InfluxDBClient', return_value=influxdb_client_mock):
            service = InfluxDBService(
                site_service=site_service_mock,
                influx_url="https://example.com",
                influx_token="test-token",
                influx_org="test-org",
                influx_bucket="test-bucket",

            )
            return service

    def test_init(self, influxdb_service, site_service_mock, influxdb_client_mock):
        """Test initialization of InfluxDBService."""
        assert influxdb_service.site_service == site_service_mock
        assert influxdb_service.influx_client == influxdb_client_mock
        assert influxdb_service.bucket == "test-bucket"
        assert influxdb_service.org == "test-org"
        # influxdb_client_mock.write_api.assert_called_once()

    def test_close(self, influxdb_service, influxdb_client_mock):
        """Test the close method."""
        influxdb_service.close()
        influxdb_client_mock.close.assert_called_once()

    @patch('vrm_client.services.influxdb_service.Point')
    def test_sync_live_data(self, mock_point, influxdb_service, site_service_mock):
        """Test syncing live data to InfluxDB."""
        # Create test energy data
        test_data = [
            EnergyData(
                installation=MagicMock(name="Site 1",id=1),
                timestamp=datetime(2023, 1, 1, 12, 0),
                consumption=2.5,
                ac_load=1.8,
                grid=0.7,
                solar=3.2,
                battery=BatteryData(
                    timestamp=datetime(2023, 1, 1, 12, 0),
                    soc=85.0,
                    voltage=52.4
                )
            ),
            EnergyData(
                installation=MagicMock(name="Site 2",id=2),
                timestamp=datetime(2023, 1, 1, 12, 0),
                consumption=1.5,
                ac_load=1.2,
                grid=-0.3,
                solar=1.8,
                battery=BatteryData(
                    timestamp=datetime(2023, 1, 1, 12, 0),
                    soc=92.0,
                    voltage=54.1
                )
            )
        ]

        site_service_mock.data.return_value = test_data
        write_api_mock = MagicMock()
        influxdb_service.influx_client.write_api.return_value = write_api_mock

        influxdb_service.sync_live_data()

        site_service_mock.data.assert_called_once()
        assert write_api_mock.write.call_once()
        args, kwargs = write_api_mock.write.call_args
        assert kwargs['bucket'] == "test-bucket"
        assert kwargs['org'] == "test-org"
        assert isinstance(kwargs['record'], list)
        assert len(kwargs['record']) == 2 + 1  # 2 points + 1 sum point

    def test_create_data_point_error(self, influxdb_service):
        """Test the _create_data_point method raising an AttributeError."""
        energy_data = EnergyData(
            installation=MagicMock(name="Test Site", id=1),
            timestamp=datetime(2023, 1, 1, 12, 0),
            consumption=2.5,
            ac_load=1.8,
            grid=0.7,
            solar=3.2,
            battery=BatteryData(
                timestamp=datetime(2023, 1, 1, 12, 0),
                soc=85.0,
                voltage=52.4
            )
        )

        from influxdb_client.client.influxdb_client import InfluxDBClient
        influxdb_service.influx_client = InfluxDBClient(
            url="https://example.com",
            token="test-token",
            org="test-org",
        )
        point = influxdb_service._create_data_point(energy_data)
        assert "site" in point._tags

    def test_create_sum_of_data_points(self, influxdb_service):
        """Test the _create_sum_of_data_points method properly aggregates field values."""
        # Create mock points with fields
        point1 = MagicMock()
        point1._fields = {"consumption": 2.5, "solar": 3.2, "grid": 0.6, "battery_voltage": 51.3, "battery_soc": 85.0}

        point2 = MagicMock()
        point2._fields = {"consumption": 1.5, "solar": None, "grid": -0.3, "battery_voltage": 54.1, "battery_soc": 92.0}

        points = [point1, point2]

        # Call the method
        result = influxdb_service._create_sum_of_data_points(points)

        # Assert the result is a Point object
        from influxdb_client.client.write.point import Point
        assert isinstance(result, Point)
        # Assert the fields are aggregated correctly
        assert result._fields["consumption"] == 4.0
        assert result._fields["solar"] == 3.2
        assert result._fields["grid"] == 0.3
        # Assert the average fields are calculated correctly
        assert result._fields["battery_voltage"] == (51.3 + 54.1) / 2
        assert result._fields["battery_soc"] == (85.0 + 92.0) / 2

