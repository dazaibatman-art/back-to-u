from flask import render_template
from app.models import Item
from app.main import main_bp


@main_bp.route("/")
def index():
    """
    Homepage preserving original hero layout, call-to-actions,
    the four core feature cards, recent public items, and configurable team section.
    """
    # Fetch recent active items for the homepage showcase
    recent_items = Item.query.filter_by(
        moderation_status="approved",
        status="active"
    ).order_by(Item.date_found.desc(), Item.created_at.desc()).limit(6).all()

    return render_template("index.html", recent_items=recent_items)


@main_bp.route("/about")
def about():
    """About Us and Team information for Group No1."""
    return render_template("about.html")


@main_bp.route("/terms")
def terms():
    """Terms of service and legal disclaimer."""
    return render_template("terms.html")


@main_bp.route("/privacy")
def privacy():
    """Privacy policy explaining data protection and private verification details."""
    return render_template("privacy.html")
