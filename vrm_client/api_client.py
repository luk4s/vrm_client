import requests
import json
import time
import logging
from typing import Dict, Optional, List
from vrm_client.config import (
    VRM_API_BASE_URL,
    VRM_API_VERSION,
    VRM_USERNAME,
    VRM_PASSWORD,
    VRM_AUTH_TOKEN,
    VRM_AUTH_MODE,
    TOKEN_CACHE_FILE
)
from vrm_client.models import User
from vrm_client.models import Installation

logger = logging.getLogger(__name__)


class VRMApiClient:
    """Client for interacting with the Victron Energy VRM API."""

    def __init__(self, auth_token: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None,
                 auth_mode: Optional[str] = None):
        """Initialize the VRM API client.

        Args:
            auth_token: VRM API auth token (preferred auth method)
            username: VRM portal username/email (alternative auth method)
            password: VRM portal password (alternative auth method)
            auth_mode: Authentication mode - "token" or "credentials"
        """
        self.base_url = f"{VRM_API_BASE_URL}/{VRM_API_VERSION}"

        # Authentication setup
        self.auth_token = auth_token or VRM_AUTH_TOKEN
        self.username = username or VRM_USERNAME
        self.password = password or VRM_PASSWORD
        self.auth_mode = auth_mode or VRM_AUTH_MODE

        # For credential-based auth
        self.session_token = None
        self.token_expires_at = 0

        # Validate authentication configuration
        if self.auth_mode == "token" and not self.auth_token:
            raise ValueError("Auth token must be provided when using token authentication mode")
        elif self.auth_mode == "credentials" and (not self.username or not self.password):
            raise ValueError("Username and password must be provided when using credentials authentication mode")

        # Try to load cached session token for credential-based auth
        if self.auth_mode == "credentials":
            self._load_cached_token()

        # Cache
        self._user = None

    def _load_cached_token(self) -> None:
        """Load session token from cache file if available and not expired."""
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cache_data = json.load(f)

            if cache_data.get("expires_at", 0) > time.time() + 60:  # Add 60s buffer
                self.session_token = cache_data.get("token")
                self.token_expires_at = cache_data.get("expires_at")
                logger.debug("Loaded session token from cache")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_token_to_cache(self) -> None:
        """Save session token to cache file."""
        if self.session_token and self.token_expires_at:
            try:
                with open(TOKEN_CACHE_FILE, "w") as f:
                    json.dump({
                        "token": self.session_token,
                        "expires_at": self.token_expires_at
                    }, f)
                logger.debug("Saved session token to cache")
            except Exception as e:
                logger.warning(f"Failed to save token to cache: {e}")

    def authenticate(self) -> None:
        """Authenticate with the VRM API if using credentials auth mode."""
        # Skip authentication if using token-based auth
        if self.auth_mode == "token":
            return

        # Skip if we already have a valid session token
        if self.session_token and self.token_expires_at > time.time() + 60:  # Add 60s buffer
            return

        auth_url = f"{self.base_url}/auth/login"
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            response = requests.post(auth_url, json=payload)
            response.raise_for_status()

            data = response.json()
            self.session_token = data.get("token")
            # Calculate expiration time (token valid for 24 hours)
            self.token_expires_at = time.time() + 24 * 60 * 60

            # Save token to cache
            self._save_token_to_cache()

            logger.info("Successfully authenticated with VRM API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated request to VRM API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: URL parameters
            data: Request body for POST/PUT requests

        Returns:
            API response as a dictionary
        """
        # Ensure we have a valid auth token if using credentials
        if self.auth_mode == "credentials":
            self.authenticate()

        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Set authorization header based on auth mode
        if self.auth_mode == "token":
            headers["X-Authorization"] = f"Token {self.auth_token}"
        else:  # credentials mode
            headers["X-Authorization"] = f"Bearer {self.session_token}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            )

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401 and self.auth_mode == "credentials":
                # Session token might have expired, invalidate and retry once
                logger.warning("Session token expired, reauthenticating...")
                self.session_token = None
                self.authenticate()

                # Update header with new session token
                headers["X-Authorization"] = f"Bearer {self.session_token}"

                # Retry the request with new token
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()

            logger.error(f"API request failed: {e}")
            raise

    def user(self) -> User:
        """Get user information.

        Returns:
            User object
        """
        if self._user:
            return self._user
        response = self._make_request("GET", "users/me")
        user_data = response.get("user", {})
        self._user = User(
            id=user_data.get("id"),
            name=user_data.get("name"),
            email=user_data.get("email")
        )
        return self._user

    def installations(self) -> List["Installation"]:
        """Get a list of all installations for the user.

        Returns:
            List of Installation objects
        """
        from vrm_client.models import Installation

        response = self._make_request("GET", f"users/{self.user().id}/installations")
        installations = []

        for record in response.get("records", []):
            installation = Installation(
                id=record.get("idSite"),
                identifier=record.get("identifier"),
                name=record.get("name"),
                timezone=record.get("timezone", "UTC"),
            )
            installations.append(installation)

        return installations
