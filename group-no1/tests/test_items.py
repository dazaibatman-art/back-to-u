import io
from app.models import Item, ItemImage
from app.extensions import db


def test_create_valid_item(client, test_user):
    """Test creating a valid found item report saves to database."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})

    response = client.post("/items/report", data={
        "name": "Silver Stainless Water Bottle",
        "category": "accessories",
        "public_description": "Silver Hydroflask left near gym benches.",
        "private_verification_details": "Has a yellow mountain sticker on the bottom base.",
        "location_found": "City Fitness Gym",
        "date_found": "2025-01-10"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Found item reported successfully" in response.data

    item = Item.query.filter_by(name="Silver Stainless Water Bottle").first()
    assert item is not None
    assert item.finder_id == test_user.id
    assert item.category == "accessories"
    assert item.status == "active"


def test_reject_invalid_item_data(client, test_user):
    """Test form validation catches missing required fields."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})

    response = client.post("/items/report", data={
        "name": "",
        "category": "",
        "public_description": "short",
        "private_verification_details": "",
        "location_found": ""
    })

    assert response.status_code == 200
    assert b"Item name is required" in response.data


def test_search_by_keyword(client, test_item):
    """Test searching items by keyword in name or description."""
    response = client.get("/search?q=Wallet")
    assert response.status_code == 200
    assert b"Blue Leather Wallet" in response.data

    response_none = client.get("/search?q=Motorcycle")
    assert response_none.status_code == 200
    assert b"No matching items found" in response_none.data


def test_filter_by_location(client, test_item):
    """Test filtering items by location."""
    response = client.get("/search?location=Library")
    assert response.status_code == 200
    assert b"Blue Leather Wallet" in response.data

    response_miss = client.get("/search?location=Tokyo")
    assert response_miss.status_code == 200
    assert b"No matching items found" in response_miss.data


def test_filter_by_category(client, test_item):
    """Test filtering items by category."""
    response = client.get("/search?category=accessories")
    assert response.status_code == 200
    assert b"Blue Leather Wallet" in response.data

    response_diff = client.get("/search?category=jewelry")
    assert response_diff.status_code == 200
    assert b"No matching items found" in response_diff.data


def test_combined_filters(client, test_item):
    """Test combining keyword, location, and category filters."""
    response = client.get("/search?q=Wallet&location=Library&category=accessories")
    assert response.status_code == 200
    assert b"Blue Leather Wallet" in response.data


def test_private_verification_protection(client, test_item, test_user):
    """
    CRITICAL SECURITY TEST: Ensure private verification details are NOT exposed to public
    or non-owner users.
    """
    # 1. Anonymous visitor
    res_anon = client.get(f"/items/{test_item.id}")
    assert res_anon.status_code == 200
    assert b"Blue Leather Wallet" in res_anon.data
    # Confidential detail must NOT be in public page
    assert b"Contains driver license ending 3381" not in res_anon.data

    # 2. Authenticated non-owner
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    res_user = client.get(f"/items/{test_item.id}")
    assert b"Contains driver license ending 3381" not in res_user.data


def test_owner_can_see_private_verification(client, test_item, test_finder):
    """Ensure authorized finder CAN view their own verification details."""
    client.post("/login", data={"email": test_finder.email, "password": "Password123!"})
    res_owner = client.get(f"/items/{test_item.id}")
    assert res_owner.status_code == 200
    assert b"Contains driver license ending 3381" in res_owner.data


def test_unauthorized_edit_rejection(client, test_item, test_user):
    """Ensure another user cannot edit an item they did not report."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})
    response = client.get(f"/items/{test_item.id}/edit")
    assert response.status_code == 403


def test_upload_valid_image(client, test_user):
    """Test uploading an image with a found item."""
    client.post("/login", data={"email": test_user.email, "password": "Password123!"})

    dummy_image = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"), "test.png")

    response = client.post("/items/report", data={
        "name": "Found Keychain with Photo",
        "category": "accessories",
        "public_description": "Found keychain with photo pendant.",
        "private_verification_details": "Photo inside is an elderly couple.",
        "location_found": "Mall food court",
        "date_found": "2025-01-12",
        "images": [dummy_image]
    }, follow_redirects=True, content_type="multipart/form-data")

    assert response.status_code == 200

    item = Item.query.filter_by(name="Found Keychain with Photo").first()
    assert item is not None
    assert len(item.images) == 1
    assert item.images[0].original_filename == "test.png"
