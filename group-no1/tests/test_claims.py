from app.models import Claim, Notification, Message, Item
from app.extensions import db


def test_submit_claim_authenticated(client, test_item, test_user):
    """Test authenticated user can submit an ownership claim."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})

    response = client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "I lost this wallet while studying at the library.",
        "evidence_details": "My license ends with 3381 and there is a library card inside."
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"ownership claim has been submitted" in response.data

    claim = Claim.query.filter_by(item_id=test_item.id, claimant_id=test_user.id).first()
    assert claim is not None
    assert claim.status == "Pending"
    assert claim.evidence_details == "My license ends with 3381 and there is a library card inside."

    # Verify finder received a notification
    notif = Notification.query.filter_by(recipient_id=test_item.finder_id).first()
    assert notif is not None
    assert "Ownership Claim" in notif.title


def test_unauthenticated_claim_redirects(client, test_item):
    """Test unauthenticated visitors are redirected to login with notice."""
    response = client.get(f"/items/{test_item.id}/claim")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_prevent_claiming_own_item(client, test_item, test_finder):
    """Test user cannot claim an item they reported finding."""
    client.post("/login", data={"email": test_finder.email, "password": "Password123!"})

    response = client.get(f"/items/{test_item.id}/claim", follow_redirects=True)
    assert response.status_code == 200
    assert b"cannot submit a claim for an item you reported" in response.data


def test_prevent_duplicate_active_claims(client, test_item, test_user):
    """Test preventing duplicate active claims on the same item."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})

    # Submit first claim
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "First claim message.",
        "evidence_details": "Proof details."
    })

    # Attempt second claim
    response = client.get(f"/items/{test_item.id}/claim", follow_redirects=True)
    assert response.status_code == 200
    assert b"already have an active claim" in response.data


def test_unauthorized_claim_detail_access(client, test_item, test_user, user_factory):
    """Test object-level authorization: an unrelated 3rd user cannot view someone else's claim."""
    # Submit claim as test_user
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "Original claim message.",
        "evidence_details": "Secret evidence."
    })

    claim = Claim.query.filter_by(item_id=test_item.id, claimant_id=test_user.id).first()
    claim_id = claim.id

    # Log out test_user first
    client.post("/logout")

    # Log in as 3rd unrelated user
    third_party = user_factory(email="stranger@example.com", full_name="Stranger")
    client.post("/login", data={"email": third_party.email, "password": "Password123!"})

    # Attempt to access claim detail
    response = client.get(f"/claims/{claim_id}")
    assert response.status_code == 403


def test_approve_claim_workflow(client, test_item, test_user, test_finder):
    """Test finder reviewing and approving claim."""
    # User submits claim
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "My wallet.",
        "evidence_details": "License ends in 3381."
    })

    claim = Claim.query.filter_by(item_id=test_item.id).first()
    claim_id = claim.id

    # Log out claimant first
    client.post("/logout")

    # Finder logs in and reviews claim
    client.post("/login", data={"email": test_finder.email, "password": "Password123!"})
    response = client.post(f"/claims/{claim_id}/review", data={
        "action": "Approved",
        "review_notes": "Evidence matches the driver license inside."
    }, follow_redirects=True)

    assert response.status_code == 200

    updated_claim = db.session.get(Claim, claim_id)
    assert updated_claim.status == "Approved"
    assert updated_claim.item.status == "claimed"

    # Verify claimant received status notification
    notif = Notification.query.filter_by(recipient_id=test_user.id).first()
    assert notif is not None
    assert "Approved" in notif.message


def test_complete_return_workflow(client, test_item, test_user, test_finder):
    """Test completing an item return updates status to 'Completed' and item to 'returned'."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "My wallet.",
        "evidence_details": "Proof."
    })

    claim = Claim.query.filter_by(item_id=test_item.id).first()
    claim_id = claim.id

    client.post("/logout")

    # Finder approves
    client.post("/login", data={"email": test_finder.email, "password": "Password123!"})
    client.post(f"/claims/{claim_id}/review", data={"action": "Approved", "review_notes": "All good."})

    # Finder completes return
    res_complete = client.post(f"/claims/{claim_id}/complete", follow_redirects=True)
    assert res_complete.status_code == 200
    assert b"marked as Completed" in res_complete.data

    updated_claim = db.session.get(Claim, claim_id)
    assert updated_claim.status == "Completed"
    assert updated_claim.item.status == "returned"


def test_in_app_messaging(client, test_item, test_user, test_finder):
    """Test safe communication between claimant and finder."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    client.post(f"/items/{test_item.id}/claim", data={
        "claim_message": "My wallet.",
        "evidence_details": "Proof."
    })

    claim = Claim.query.filter_by(item_id=test_item.id).first()
    claim_id = claim.id

    # Claimant sends a message
    response = client.post(f"/claims/{claim_id}/messages", data={
        "content": "Can we meet at the campus safety desk tomorrow at 2 PM?"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Message sent safely" in response.data

    msg = Message.query.filter_by(claim_id=claim_id).first()
    assert msg is not None
    assert msg.sender_id == test_user.id
    assert msg.recipient_id == test_finder.id
    assert "campus safety desk" in msg.content
