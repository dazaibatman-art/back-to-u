from flask import jsonify, request, abort
from app.models import Item
from app.api import api_bp


@api_bp.route("/items/<int:item_id>")
def get_item(item_id: int):
    """
    Return sanitized public item details for dynamic modal view.
    CRITICAL: Never exposes private_verification_details.
    """
    item = Item.query.get_or_404(item_id)

    if item.moderation_status != "approved":
        abort(404)

    return jsonify({
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "location": item.location_found,
        "date_found": item.date_found.strftime("%Y-%m-%d"),
        "description": item.public_description,
        "finder_name": item.finder_display_name,
        "status": item.status,
        "status_label": item.status_label,
        "image_url": item.primary_image_url,
        "images": item.image_urls
    })


@api_bp.route("/search")
def search_items():
    """Live search API returning items matching query filters."""
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    category = request.args.get("category", "").strip().lower()

    stmt = Item.query.filter_by(moderation_status="approved")

    if query:
        search_filter = f"%{query}%"
        stmt = stmt.filter((Item.name.ilike(search_filter)) | (Item.public_description.ilike(search_filter)))

    if location:
        stmt = stmt.filter(Item.location_found.ilike(f"%{location}%"))

    if category and category in Item.VALID_CATEGORIES:
        stmt = stmt.filter_by(category=category)

    items = stmt.order_by(Item.date_found.desc()).limit(30).all()

    return jsonify({
        "count": len(items),
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "location": item.location_found,
                "date_found": item.date_found.strftime("%Y-%m-%d"),
                "description": item.public_description,
                "finder_name": item.finder_display_name,
                "status": item.status,
                "status_label": item.status_label,
                "image_url": item.primary_image_url
            }
            for item in items
        ]
    })
