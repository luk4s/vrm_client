from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class User:
    id: str
    name: str
    email: str


@dataclass
class Installation:
    id: int
    identifier: str
    name: str
    timezone: str

@dataclass
class BatteryData:
    timestamp: datetime
    soc: float
    voltage: float
    current: Optional[float] = None
    power: Optional[float] = None
    temperature: Optional[float] = None

@dataclass
class EnergyData:
    timestamp: datetime
    installation: Installation
    ac_load: float
    grid: float
    consumption: float
    solar: Optional[float] = None
    battery: Optional[BatteryData] = None

    @property
    def name(self) -> str:
        return self.installation.name

    @property
    def installation_id(self) -> int:
        return self.installation.id