import sys
from pathlib import Path
import pytest

# Ensure group-no1 directory is on python sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.models import User, Item, Claim, Notification, Message


@pytest.fixture
def app():
    """Create application configured for testing."""
    test_app = create_app("testing")
    ctx = test_app.app_context()
    ctx.push()

    db.create_all()

    yield test_app

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def user_factory():
    """Factory fixture to create test users within active session."""
    def _create_user(email="testuser@example.com", password="Password123!", full_name="Test User", role="user"):
        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return _create_user


@pytest.fixture
def test_user(user_factory):
    """Default test user fixture."""
    return user_factory(email="member@example.com", full_name="Regular Member")


@pytest.fixture
def test_finder(user_factory):
    """Finder user fixture."""
    return user_factory(email="finder@example.com", full_name="Finder User")


@pytest.fixture
def test_item(test_finder):
    """Sample lost & found item fixture."""
    item = Item(
        name="Blue Leather Wallet",
        category="accessories",
        public_description="Blue bi-fold leather wallet found near Central Library.",
        private_verification_details="Contains driver license ending 3381 and silver card.",
        location_found="Central Library",
        status="active",
        moderation_status="approved",
        finder_id=test_finder.id,
        finder_display_name=test_finder.full_name
    )
    db.session.add(item)
    db.session.commit()
    return item
