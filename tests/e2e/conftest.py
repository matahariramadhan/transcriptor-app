import pytest
import os
from dotenv import load_dotenv
from pathlib import Path

# Define project root relative to this conftest.py
PROJECT_ROOT = Path(__file__).parent.parent.parent

@pytest.fixture(scope="session", autouse=True)
def load_env_vars(request):
    """
    Loads environment variables from the .env file in the project root
    before any tests in this session run.
    'autouse=True' makes it run automatically for the session.
    """
    dotenv_path = PROJECT_ROOT / ".env"
    print(f"\nAttempting to load .env file from: {dotenv_path}") # Debug print
    loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True)
    if loaded:
        print(".env file loaded successfully by fixture.")
    else:
        print(".env file not found or empty.")
    # No need to return anything
