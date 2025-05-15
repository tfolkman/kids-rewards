import pytest
from fastapi.testclient import TestClient

from backend.main import (
    app,  # Corrected import: Assuming FastAPI app is in main.py at the root of the backend directory
)


@pytest.fixture(scope="module")
def client():
    """
    Yield a TestClient instance that can be used to send requests to the application.
    """
    with TestClient(app) as c:
        yield c


# You can add more fixtures here as needed, for example, for database setup/teardown
# or for creating mock services.

# Example fixture for a mock database (replace with your actual setup if needed)
# @pytest.fixture(scope="function")
# def mock_db_session():
#     print("Setting up mock DB session")
#     # Setup mock database or use a test database
#     db = ... # Your mock/test database connection
#     yield db
#     print("Tearing down mock DB session")
#     # Teardown mock database
#     db.close()
