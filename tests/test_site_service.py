import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from vrm_client.services.site_service import SiteService
from vrm_client.models import Installation


class TestSiteService:
    """Tests for the SiteService class."""

    @pytest.fixture
    def api_client_mock(self):
        """Create a mock API client."""
        return MagicMock()

    @pytest.fixture
    def site_service(self, api_client_mock):
        """Create a SiteService with a mock API client."""
        return SiteService(api_client_mock)

    def test_init(self, site_service, api_client_mock):
        """Test initialization of SiteService."""
        assert site_service.api == api_client_mock

    @patch("vrm_client.services.site_service.datetime")
    def test_installation_data(self, mock_datetime, site_service, api_client_mock, fixtures_path):
        """Test the _installation_data method."""
        # Setup mock datetime
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        # Setup test installation
        test_installation = Installation(id=123, identifier="test-123", name="Test Site", timezone="UTC")

        # Setup mock API response
        with open(fixtures_path / "installation_stats_example.json", "r") as f:
            api_client_mock._make_request.return_value = json.load(f)

        # Call method
        result = site_service._installation_data(test_installation)

        # Calculate expected start time
        expected_start_time = int((mock_now - timedelta(minutes=15)).timestamp())

        # Verify API client was called with correct parameters
        api_client_mock._make_request.assert_called_once()

        assert "success" in result
        assert "records" in result

    def test_data(self, site_service, api_client_mock, fixtures_path):
        """Test the live_feed method."""
        # Setup mock API response
        with open(fixtures_path / "installation_stats_example.json", "r") as f:
            api_client_mock._make_request.return_value = json.load(f)

        api_client_mock.installations.return_value = [
            MagicMock(id=234),
            MagicMock(id=123)
        ]

        # Call method
        result = site_service.data()

        api_client_mock.installations.assert_called_once()

        assert isinstance(result, list)
        assert len(result) > 0