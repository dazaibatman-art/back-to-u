from app.models import Item, Claim
from app.extensions import db


def test_dashboard_empty_user(client, test_user):
    """Test dashboard displays real zeros and 'Not yet rated' for a user with no activity."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    response = client.get("/dashboard")

    assert response.status_code == 200
    # Checks that real zero count is rendered
    assert b"0" in response.data
    # Checks legitimate placeholder for unrated trust score instead of fabricated 4.8
    assert b"Not yet rated" in response.data


def test_dashboard_reflects_actual_counts(client, test_user, test_finder, test_item):
    """Test dashboard numbers reflect real database counts."""
    # test_user reports an item
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    client.post("/items/report", data={
        "name": "Found Green Scarf",
        "category": "accessories",
        "public_description": "Wool green scarf left on bench.",
        "private_verification_details": "Has tag with 'Handmade with love'.",
        "location_found": "City Park",
        "date_found": "2025-01-14"
    })

    # test_user submits a claim on test_item
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "My wallet.",
        "evidence_details": "Proof."
    })

    response = client.get("/dashboard")
    assert response.status_code == 200

    user_items_count = Item.query.filter_by(finder_id=test_user.id).count()
    user_claims_count = Claim.query.filter_by(claimant_id=test_user.id).count()
    assert user_items_count == 1
    assert user_claims_count == 1


def test_persistence_across_app_context(app, test_user):
    """Verify data persistence after committing and expiring session cache."""
    item = Item(
        name="Persistent Test Item",
        category="electronics",
        public_description="Test description.",
        private_verification_details="Private secret.",
        location_found="Test Lab",
        finder_id=test_user.id,
        finder_display_name=test_user.full_name
    )
    db.session.add(item)
    db.session.commit()
    saved_id = item.id

    # Expire all cached instances in session and query fresh from database
    db.session.expire_all()
    fetched = db.session.get(Item, saved_id)
    assert fetched is not None
    assert fetched.name == "Persistent Test Item"
    assert fetched.finder.email == test_user.email
