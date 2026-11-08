from flask import render_template
from flask_login import current_user, login_required
from app.models import Item, Claim, Notification
from app.dashboard import dashboard_bp


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """
    Main user dashboard showing real database counts, calculated trust score,
    and recent activity stream.
    """
    # Real database queries for authenticated user
    found_items_count = Item.query.filter_by(finder_id=current_user.id).count()
    claims_count = Claim.query.filter_by(claimant_id=current_user.id).count()
    trust_score_display = current_user.trust_score_display

    # Recent items reported by user
    recent_items = Item.query.filter_by(finder_id=current_user.id)\
        .order_by(Item.created_at.desc()).limit(5).all()

    # Recent claims submitted by user
    recent_claims = Claim.query.filter_by(claimant_id=current_user.id)\
        .order_by(Claim.created_at.desc()).limit(5).all()

    # Incoming claims waiting for review on items found by user
    incoming_claims = Claim.query.join(Item).filter(Item.finder_id == current_user.id)\
        .order_by(Claim.created_at.desc()).limit(5).all()

    # Recent notifications
    recent_notifications = Notification.query.filter_by(recipient_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        found_items_count=found_items_count,
        claims_count=claims_count,
        trust_score_display=trust_score_display,
        recent_items=recent_items,
        recent_claims=recent_claims,
        incoming_claims=incoming_claims,
        recent_notifications=recent_notifications
    )


@dashboard_bp.route("/dashboard/items")
@login_required
def my_items():
    """Detailed management view for all items reported by current user."""
    items = Item.query.filter_by(finder_id=current_user.id)\
        .order_by(Item.created_at.desc()).all()
    return render_template("my_items.html", items=items)


@dashboard_bp.route("/dashboard/claims")
@login_required
def my_claims():
    """Detailed view of all claims submitted by current user."""
    claims = Claim.query.filter_by(claimant_id=current_user.id)\
        .order_by(Claim.created_at.desc()).all()
    return render_template("my_claims.html", claims=claims)
