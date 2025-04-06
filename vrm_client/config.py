import os

# API Configuration
VRM_API_BASE_URL = "https://vrmapi.victronenergy.com"
VRM_API_VERSION = "v2"

# Authentication
# Support for both token-based and username/password auth
VRM_AUTH_TOKEN = os.getenv("VRM_AUTH_TOKEN")  # Token-based auth (preferred)
VRM_USERNAME = os.getenv("VRM_USERNAME")      # Username/password auth (fallback)
VRM_PASSWORD = os.getenv("VRM_PASSWORD")

# Auth mode can be "token" or "credentials"
VRM_AUTH_MODE = os.getenv("VRM_AUTH_MODE", "token" if VRM_AUTH_TOKEN else "credentials")

# Optional: Token caching (for username/password auth only)
TOKEN_CACHE_FILE = ".vrm_token_cache"

# InfluxDB Configuration
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

# Default data collection interval in seconds
DATA_COLLECTION_INTERVAL = int(os.getenv("DATA_COLLECTION_INTERVAL", 5))

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Email settings for reports (optional)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
REPORT_RECIPIENT = os.getenv("REPORT_RECIPIENT")