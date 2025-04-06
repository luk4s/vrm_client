import pytest
import json
import time
from unittest.mock import patch, MagicMock, mock_open
from vrm_client.api_client import VRMApiClient

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

    @patch("vrm_client.api_client.requests.post")
    def test_authenticate(self, mock_post, api_client_credentials):
        """Test the authenticate method."""
        mock_response = MagicMock()
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

    @patch("vrm_client.api_client.open", new_callable=mock_open)
    @patch("vrm_client.api_client.json.dump")
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

    @patch("vrm_client.api_client.open", new_callable=mock_open)
    @patch("vrm_client.api_client.json.load")
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

    @patch("vrm_client.api_client.requests.request")
    def test_make_request_token_auth(self, mock_request, api_client_token):
        """Test making API requests with token authentication."""
        mock_response = MagicMock()
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
        assert kwargs["headers"]["X-Authorization"] == "Token test-token"

        # Verify result
        assert result == {"data": "test-data"}

    @patch("vrm_client.api_client.requests.request")
    def test_make_request_credentials_auth(self, mock_request, api_client_credentials):
        """Test making API requests with credentials authentication."""
        # Setup mock session token
        api_client_credentials.session_token = "test-session-token"
        api_client_credentials.token_expires_at = time.time() + 3600

        # Setup mock response
        mock_response = MagicMock()
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

    @patch("vrm_client.api_client.VRMApiClient._make_request")
    @patch("vrm_client.api_client.VRMApiClient.user")
    def test_installations(self, mock_user, mock_make_request, api_client_token, fixtures_path):
        """Test get_installations method."""
        from vrm_client.models import User, Installation

        mock_user_obj = User(id=3, name="Test User", email="test@example.com")
        mock_user.return_value = mock_user_obj

        # Setup mock
        with open(fixtures_path / "user_all_installation_example.json", "r") as f:
            mock_make_request.return_value = json.load(f)

        # Call method
        result = api_client_token.installations()

        # Verify request
        mock_make_request.assert_called_once_with("GET", "users/3/installations")
        assert isinstance(result, list)
        assert all(isinstance(item, Installation) for item in result)

    @patch("vrm_client.api_client.VRMApiClient._make_request")
    def test_user(self, mock_make_request, api_client_token, fixtures_path):
        from vrm_client.models import User

        with open(fixtures_path / "user_me_example.json", "r") as f:
            mock_make_request.return_value = json.load(f)

        result = api_client_token.user()
        mock_make_request.assert_called_once_with("GET", "users/me")

        # Verify result is a User instance
        assert isinstance(result, User)

        # Verify properties were set correctly
        assert result.id == 1
        assert result.name == "Lukas"
        assert result.email == "admin@luk4s.cz"

        mock_make_request.reset_mock()
        cached_result = api_client_token.user()
        mock_make_request.assert_not_called()
        assert cached_result is result