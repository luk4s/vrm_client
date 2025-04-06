# conftest.py (place in your tests directory)
import os
import json
import pytest
from pathlib import Path

@pytest.fixture
def fixtures_path():
    """Return the absolute path to the fixtures directory."""
    return Path(os.path.dirname(__file__)) / "fixtures"

@pytest.fixture
def load_fixture():
    """Return a function that loads JSON fixture files."""
    def _load_fixture(filename):
        fixtures_dir = Path(os.path.dirname(__file__)) / "fixtures"
        with open(fixtures_dir / filename, "r") as f:
            return json.load(f)
    return _load_fixture