from flask import render_template, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Notification
from app.notifications import notifications_bp


@notifications_bp.route("/notifications")
@login_required
def index():
    """Display all notifications for the current user."""
    notifications = Notification.query.filter_by(recipient_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notifications=notifications)


@notifications_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id: int):
    """Mark a single notification as read."""
    notif = Notification.query.filter_by(id=notification_id, recipient_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read for current user."""
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/api/notifications/unread-count")
@login_required
def unread_count():
    """Return JSON unread notification count for dynamic navbar badge."""
    count = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({"unread_count": count})
