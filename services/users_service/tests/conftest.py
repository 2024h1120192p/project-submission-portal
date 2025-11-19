import sys
import os
import pytest

# monorepo root: Project/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def reset_user_store():
    """Clear the user store before each test to ensure test isolation."""
    from services.users_service.app.store import store
    store.users.clear()
    yield
    store.users.clear()
