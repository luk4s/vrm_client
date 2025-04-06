import pytest
import json
import time
from unittest.mock import patch, MagicMock, mock_open

from api_client import VRMApiClient


class TestVRMApiClient:
    """Tests for the VRMApiClient class."""

    @pytest.fixture
    def api_client_token(self):
        """Create a VRMApiClient instance with token auth."""
        return VRMApiClient(auth_token="test-token", auth_mode="token")

    @pytest.fixture
    def api_client_credentials(self):
        """Create a VRMApiClient instance with credentials auth."""
        return VRMApiClient(username="test@example.com", password="password", auth_mode="credentials")

    def test_init_with_token(self, api_client_token):
        """Test initialization with token authentication."""
        assert api_client_token.auth_token == "test-token"
        assert api_client_token.auth_mode == "token"

    def test_init_with_credentials(self, api_client_credentials):
        """Test initialization with credentials authentication."""
        assert api_client_credentials.username == "test@example.com"
        assert api_client_credentials.password == "password"
        assert api_client_credentials.auth_mode == "credentials"

    def test_init_invalid_config(self):
        """Test initialization with invalid configuration."""
        # Missing token in token mode
        with pytest.raises(ValueError):
            VRMApiClient(auth_mode="token")

        # Missing credentials in credentials mode
        with pytest.raises(ValueError):
            VRMApiClient(auth_mode="credentials")

    @patch("api_client.requests.post")
    def test_authenticate(self, mock_post, api_client_credentials, mock_response):
        """Test the authenticate method."""
        # Setup mock response
        mock_response.json.return_value = {"token": "mock-session-token"}
        mock_post.return_value = mock_response

        # Call authenticate
        api_client_credentials.authenticate()

        # Verify the API was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["username"] == "test@example.com"
        assert kwargs["json"]["password"] == "password"

        # Verify the token was stored
        assert api_client_credentials.session_token == "mock-session-token"
        assert api_client_credentials.token_expires_at > time.time()

    @patch("api_client.open", new_callable=mock_open)
    @patch("api_client.json.dump")
    def test_save_token_to_cache(self, mock_json_dump, mock_file_open, api_client_credentials):
        """Test saving token to cache."""
        # Setup test data
        api_client_credentials.session_token = "test-session-token"
        api_client_credentials.token_expires_at = time.time() + 86400  # 24 hours from now

        # Call the method
        api_client_credentials._save_token_to_cache()

        # Verify file operations
        mock_file_open.assert_called_once_with(".vrm_token_cache", "w")
        mock_json_dump.assert_called_once()
        args, kwargs = mock_json_dump.call_args
        assert args[0]["token"] == "test-session-token"
        assert args[0]["expires_at"] == api_client_credentials.token_expires_at

    @patch("api_client.open", new_callable=mock_open)
    @patch("api_client.json.load")
    def test_load_cached_token(self, mock_json_load, mock_file_open, api_client_credentials):
        """Test loading token from cache."""
        # Setup test data
        expiry_time = time.time() + 86400  # 24 hours from now
        mock_json_load.return_value = {
            "token": "cached-session-token",
            "expires_at": expiry_time
        }

        # Call the method
        api_client_credentials._load_cached_token()

        # Verify file operations
        mock_file_open.assert_called_once_with(".vrm_token_cache", "r")
        mock_json_load.assert_called_once()

        # Verify token loaded
        assert api_client_credentials.session_token == "cached-session-token"
        assert api_client_credentials.token_expires_at == expiry_time

    @patch("api_client.requests.request")
    def test_make_request_token_auth(self, mock_request, api_client_token, mock_response):
        """Test making API requests with token authentication."""
        # Setup mock
        mock_response.json.return_value = {"data": "test-data"}
        mock_request.return_value = mock_response

        # Make request
        result = api_client_token._make_request("GET", "test-endpoint", {"param": "value"})

        # Verify request
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert "test-endpoint" in kwargs["url"]
        assert kwargs["params"] == {"param": "value"}
        assert kwargs["headers"]["Authorization"] == "Token test-token"

        # Verify result
        assert result == {"data": "test-data"}

    @patch("api_client.requests.request")
    def test_make_request_credentials_auth(self, mock_request, api_client_credentials, mock_response):
        """Test making API requests with credentials authentication."""
        # Setup mock session token
        api_client_credentials.session_token = "test-session-token"
        api_client_credentials.token_expires_at = time.time() + 3600

        # Setup mock response
        mock_response.json.return_value = {"data": "test-data"}
        mock_request.return_value = mock_response

        # Make request
        result = api_client_credentials._make_request("GET", "test-endpoint")

        # Verify request
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["headers"]["X-Authorization"] == "Bearer test-session-token"

        # Verify result
        assert result == {"data": "test-data"}

    @patch("api_client.requests.request")
    @patch("api_client.VRMApiClient.authenticate")
    def test_request_with_token_refresh(self, mock_authenticate, mock_request, api_client_credentials):
        """Test request with token refresh on 401 error."""
        # Setup initial failed response (401)
        failed_response = MagicMock()
        failed_response.raise_for_status.side_effect = [
            requests.exceptions.HTTPError("401 Client Error"),
            None  # Second call succeeds
        ]
        failed_response.status_code = 401

        # Setup success response for retry
        success_response = MagicMock()
        success_response.json.return_value = {"data": "refreshed-data"}

        # Return failed response first, then success response
        mock_request.side_effect = [failed_response, success_response]

        # Set expired token
        api_client_credentials.session_token = "expired-token"
        api_client_credentials.token_expires_at = time.time() - 3600

        # Mock authenticate to set a new token
        def set_new_token():
            api_client_credentials.session_token = "new-token"
            api_client_credentials.token_expires_at = time.time() + 3600

        mock_authenticate.side_effect = set_new_token

        # Make request
        result = api_client_credentials._make_request("GET", "test-endpoint")

        # Verify authenticate was called to refresh the token
        mock_authenticate.assert_called_once()

        # Verify request was called twice (first with expired token, then with new token)
        assert mock_request.call_count == 2

        # Verify second request used new token
        args, kwargs = mock_request.call_args_list[1]
        assert kwargs["headers"]["X-Authorization"] == "Bearer new-token"

        # Verify we got the success result
        assert result == {"data": "refreshed-data"}

    @patch("api_client.VRMApiClient._make_request")
    def test_get_installations(self, mock_make_request, api_client_token):
        """Test get_installations method."""
        # Setup mock
        mock_make_request.return_value = {
            "records": [{"id": 1, "name": "Test Site"}]
        }

        # Call method
        result = api_client_token.get_installations()

        # Verify request
        mock_make_request.assert_called_once_with("GET", "installations")

        # Verify result
        assert result == [{"id": 1, "name": "Test Site"}]

    @patch("api_client.VRMApiClient._make_request")
    def test_get_installation_info(self, mock_make_request, api_client_token):
        """Test get_installation_info method."""
        # Setup mock
        mock_make_request.return_value = {"id": 12345, "name": "Test Site"}

        # Call method
        result = api_client_token.get_installation_info(12345)

        # Verify request
        mock_make_request.assert_called_once_with("GET", "installations/12345")

        # Verify result
        assert result["id"] == 12345
        assert result["name"] == "Test Site"

    @patch("api_client.VRMApiClient._make_request")
    def test_get_site_overview(self, mock_make_request, api_client_token):
        """Test get_site_overview method."""
        # Setup mock
        mock_make_request.return_value = {
            "last_timestamp": 1647518450,
            "overview": {
                "pv": {"power": 1000}
            }
        }

        # Call method
        result = api_client_token.get_site_overview(12345)

        # Verify request
        mock_make_request.assert_called_once_with("GET", "installations/12345/overview")

        # Verify result
        assert result["last_timestamp"] == 1647518450
        assert result["overview"]["pv"]["power"] == 1000

    @patch("api_client.VRMApiClient._make_request")
    def test_get_devices(self, mock_make_request, api_client_token):
        """Test get_devices method."""
        # Setup mock
        mock_make_request.return_value = {
            "records": [{"id": "device1", "productName": "MultiPlus"}]
        }

        # Call method
        result = api_client_token.get_devices(12345)

        # Verify request
        mock_make_request.assert_called_once_with("GET", "installations/12345/devices")

        # Verify result
        assert result == [{"id": "device1", "productName": "MultiPlus"}]

    @patch("api_client.VRMApiClient._make_request")
    def test_get_diagnostics(self, mock_make_request, api_client_token):
        """Test get_diagnostics method."""
        # Setup mock
        mock_make_request.return_value = {"records": [{"parameter": "value"}]}

        # Call method
        result = api_client_token.get_diagnostics(12345, "device1")

        # Verify request
        mock_make_request.assert_called_once_with("GET", "installations/12345/diagnostics/device1")

        # Verify result
        assert "records" in result