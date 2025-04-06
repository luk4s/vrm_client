# VRM API Client

A Python client for the Victron Energy VRM API with InfluxDB integration for data collection and monitoring.

## Features

API client for Victron Energy's VRM API. Currently supports:
- get user info
- get installations of user
- get installation data
  - `ac_loads`: AC load power consumption (W)
  - `from_to_grid`: Grid power import/export (W)
  - `consumption`: Total energy consumption (W)
  - `solar_yield`: Solar production power (W)
  - `bs`: Battery state of charge (%)
  - `bv`: Battery voltage (V)

Data can be automatically collected and sent to InfluxDB for monitoring and analysis.
- Scheduled data collection using APScheduler
- InfluxDB integration for storing and querying data

Influx DB stores 2 measurements:
- `fve_data`: Data for each installation. Installation name and ID are stored as tags.
- `solar_system`: SUM of all installations for each data point. This is useful for monitoring the entire system.

## Requirements

- Python 3.10 or higher
- VRM API access credentials
- InfluxDB instance (local or cloud)

## Configuration

Configure the client by editing the `.env` file:

```
# VRM Authentication
VRM_AUTH_TOKEN=your_api_token

# InfluxDB Configuration
INFLUXDB_URL=https://your-influxdb-instance.com
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=your_organization
INFLUXDB_BUCKET=vrm_data

# Collection settings
DATA_COLLECTION_INTERVAL=5  # seconds
LOG_LEVEL=INFO
```

## Development

### Dependencies

- requests: HTTP client for API calls
- python-dotenv: Environment variable management
- influxdb-client: InfluxDB API client
- apscheduler: Job scheduling

### Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.