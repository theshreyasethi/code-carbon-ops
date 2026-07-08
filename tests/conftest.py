"""
Shared test fixtures for CodeCarbonOps tests.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.database.connection import engine, Base, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create a clean test database."""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for direct DB testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_inference_data():
    """Sample inference request data."""
    return {
        "prompt": "Summarize climate change impacts on agriculture",
        "model": "gpt-4",
        "carbon_budget_g": 10.0
    }
