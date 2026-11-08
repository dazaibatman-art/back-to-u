from app.models import User
from app.extensions import db


def test_successful_registration(client, app):
    """Test registering a new account successfully persists user with hashed password."""
    response = client.post("/register", data={
        "full_name": "New Member",
        "email": "newmember@example.com",
        "phone": "+1 555-0199",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    with app.app_context():
        user = User.query.filter_by(email="newmember@example.com").first()
        assert user is not None
        assert user.full_name == "New Member"
        assert user.check_password("SecurePassword123!") is True
        # Verify plaintext password was NEVER stored
        assert user.password_hash != "SecurePassword123!"


def test_duplicate_email_rejection(client, test_user):
    """Test that registering with an existing email fails."""
    response = client.post("/register", data={
        "full_name": "Another User",
        "email": test_user.email,
        "password": "Password123!",
        "confirm_password": "Password123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"already registered" in response.data


def test_successful_login(client, test_user):
    """Test logging in with valid credentials."""
    response = client.post("/login", data={
        "email": test_user.email,
        "password": "Password123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Login successful" in response.data
    assert b"Welcome" in response.data


def test_invalid_login_password(client, test_user):
    """Test login rejection when password does not match."""
    response = client.post("/login", data={
        "email": test_user.email,
        "password": "WrongPassword!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_invalid_login_nonexistent_email(client):
    """Test generic rejection for non-registered email."""
    response = client.post("/login", data={
        "email": "ghost@example.com",
        "password": "AnyPassword123!"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout(client, test_user):
    """Test logging out terminates the session."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    
    response = client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"successfully logged out" in response.data


def test_protected_routes_require_login(client):
    """Test unauthenticated requests to protected endpoints redirect to login."""
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 302
    assert "/login" in res_dash.headers["Location"]

    res_profile = client.get("/profile")
    assert res_profile.status_code == 302
    assert "/login" in res_profile.headers["Location"]

    res_notif = client.get("/notifications")
    assert res_notif.status_code == 302
    assert "/login" in res_notif.headers["Location"]
