#!/usr/bin/env python
import code

from vrm_client.api_client import VRMApiClient
from vrm_client.services.site_service import SiteService
from vrm_client.services.influxdb_service import InfluxDBService

namespace = {
    "VRMApiClient": VRMApiClient,
    "SiteService": SiteService,
    "InfluxDBService": InfluxDBService,
}
code.interact(
    banner="Python console with VRMApiClient pre-loaded as 'client'",
    local=namespace
)