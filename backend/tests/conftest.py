"""Pytest configuration and fixtures"""
import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)
