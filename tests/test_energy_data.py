from vrm_client.models import EnergyData, Installation
from datetime import datetime
import pytest


def test_installation():
    # Create a test installation
    installation = Installation(
        id=123,
        identifier="test-installation",
        name="Test Installation",
        timezone="Europe/Prague"
    )

    # Create EnergyData with the installation
    timestamp = datetime.now()
    energy_data = EnergyData(
        timestamp=timestamp,
        installation=installation,
        ac_load=100.0,
        grid=200.0,
        consumption=300.0
    )

    # Verify that the installation was correctly assigned
    assert energy_data.installation == installation
    assert energy_data.installation_id == 123
    assert energy_data.name == "Test Installation"


def test_installation_required_parameter():
    # Verify that installation is a required parameter
    timestamp = datetime.now()
    with pytest.raises(TypeError):
        EnergyData(
            timestamp=timestamp,
            ac_load=100.0,
            grid=200.0,
            consumption=300.0
        )
