from datetime import datetime, timezone, date
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
from app.extensions import db, login_manager


def utc_now() -> datetime:
    """Return current UTC datetime timezone-aware."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """User account model for authentication, trust scoring, and ownership tracking."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    show_phone_publicly = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user', 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    found_items = db.relationship(
        "Item",
        back_populates="finder",
        foreign_keys="Item.finder_id",
        lazy="select",
        cascade="all, delete-orphan"
    )
    claims = db.relationship(
        "Claim",
        back_populates="claimant",
        foreign_keys="Claim.claimant_id",
        lazy="select",
        cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification",
        back_populates="recipient",
        foreign_keys="Notification.recipient_id",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="desc(Notification.created_at)"
    )

    def set_password(self, password: str) -> None:
        """Hash and store password securely."""
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        """Verify plain password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_trust_score(self) -> Optional[float]:
        """
        Legitimate, transparent trust score calculation based on real database records.
        Returns None ('Not yet rated') if user has no completed returns or claims.
        """
        # Calculate returned items reported by user
        returned_count = sum(1 for item in self.found_items if item.status == "returned")
        active_items_count = len(self.found_items)
        
        # Calculate claim records
        completed_claims = sum(1 for claim in self.claims if claim.status == "Completed")
        approved_claims = sum(1 for claim in self.claims if claim.status == "Approved")
        rejected_claims = sum(1 for claim in self.claims if claim.status == "Rejected")

        total_interactions = active_items_count + len(self.claims)
        if total_interactions == 0:
            return None  # Displays 'Not yet rated'

        # Baseline score 4.0 for engaged members
        score = 4.0
        score += (returned_count * 0.25)
        score += (completed_claims * 0.20)
        score += (approved_claims * 0.10)
        score -= (rejected_claims * 0.30)

        # Clamp between 1.0 and 5.0
        score = max(1.0, min(5.0, score))
        return round(score, 1)

    @property
    def trust_score_display(self) -> str:
        """Formatted trust score or friendly placeholder."""
        score = self.get_trust_score()
        if score is None:
            return "Not yet rated"
        return f"{score:.1f}/5.0"

    @property
    def unread_notifications_count(self) -> int:
        """Get number of unread notifications."""
        return sum(1 for n in self.notifications if not n.is_read)

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}'>"


@login_manager.user_loader
def load_user(user_id: str) -> Optional[User]:
    """Flask-Login user loader callback."""
    if not user_id:
        return None
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


class Item(db.Model):
    """Lost and Found item reporting model."""
    __tablename__ = "items"

    VALID_CATEGORIES = ("electronics", "documents", "accessories", "bags", "jewelry", "other")
    VALID_STATUSES = ("active", "pending_claim", "claimed", "returned", "archived")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    public_description = db.Column(db.Text, nullable=False)
    
    # Private verification details: strictly protected, never shown to the public!
    private_verification_details = db.Column(db.Text, nullable=False)
    
    location_found = db.Column(db.String(200), nullable=False, index=True)
    date_found = db.Column(db.Date, nullable=False, default=date.today)
    
    status = db.Column(db.String(30), default="active", nullable=False, index=True)
    moderation_status = db.Column(db.String(30), default="approved", nullable=False, index=True)
    
    finder_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    finder_display_name = db.Column(db.String(100), default="Anonymous", nullable=False)
    
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    finder = db.relationship("User", back_populates="found_items", foreign_keys=[finder_id])
    images = db.relationship(
        "ItemImage",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ItemImage.id",
        lazy="select"
    )
    claims = db.relationship(
        "Claim",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="desc(Claim.created_at)",
        lazy="select"
    )

    @property
    def primary_image_url(self) -> str:
        """Return the primary image URL or fallback SVG/default."""
        if self.images:
            return url_for("items.serve_image", filename=self.images[0].storage_path)
        # Default placeholder category image
        return url_for("static", filename="images/placeholder.svg")

    @property
    def image_urls(self) -> list[str]:
        """Return all image URLs for this item."""
        if self.images:
            return [url_for("items.serve_image", filename=img.storage_path) for img in self.images]
        return [url_for("static", filename="images/placeholder.svg")]

    @property
    def status_badge_class(self) -> str:
        """CSS class mapping for item status."""
        mapping = {
            "active": "badge-status-active",
            "pending_claim": "badge-status-pending",
            "claimed": "badge-status-claimed",
            "returned": "badge-status-returned",
            "archived": "badge-status-archived",
        }
        return mapping.get(self.status, "badge-status-active")

    @property
    def status_label(self) -> str:
        """Human-readable status label."""
        return self.status.replace("_", " ").title()

    def __repr__(self) -> str:
        return f"<Item id={self.id} name='{self.name}' status='{self.status}'>"


class ItemImage(db.Model):
    """Item photo metadata and local storage mapping."""
    __tablename__ = "item_images"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    item = db.relationship("Item", back_populates="images")

    @property
    def url(self) -> str:
        """Return URL to serve this image."""
        return url_for("items.serve_image", filename=self.storage_path)

    def __repr__(self) -> str:
        return f"<ItemImage id={self.id} item_id={self.item_id}>"


class Claim(db.Model):
    """Ownership claim submitted for a lost item."""
    __tablename__ = "claims"

    VALID_STATUSES = ("Pending", "Under Review", "Approved", "Rejected", "Completed")

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    claimant_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    claim_message = db.Column(db.Text, nullable=False)
    evidence_details = db.Column(db.Text, nullable=False)  # Ownership proof, private details provided by claimant
    
    status = db.Column(db.String(30), default="Pending", nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    item = db.relationship("Item", back_populates="claims")
    claimant = db.relationship("User", back_populates="claims", foreign_keys=[claimant_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    messages = db.relationship(
        "Message",
        back_populates="claim",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="select"
    )

    @property
    def status_badge_class(self) -> str:
        """CSS class for claim status badge."""
        mapping = {
            "Pending": "badge-status-pending",
            "Under Review": "badge-status-review",
            "Approved": "badge-status-approved",
            "Rejected": "badge-status-rejected",
            "Completed": "badge-status-returned",
        }
        return mapping.get(self.status, "badge-status-pending")

    def __repr__(self) -> str:
        return f"<Claim id={self.id} item_id={self.item_id} claimant_id={self.claimant_id} status='{self.status}'>"


class Message(db.Model):
    """In-app communication between finder and claimant for safe handoff."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    claim = db.relationship("Claim", back_populates="messages")
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def __repr__(self) -> str:
        return f"<Message id={self.id} claim_id={self.claim_id} sender_id={self.sender_id}>"


class Notification(db.Model):
    """User notifications for claim activity and status updates."""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    related_item_id = db.Column(db.Integer, db.ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    related_claim_id = db.Column(db.Integer, db.ForeignKey("claims.id", ondelete="SET NULL"), nullable=True)
    
    notification_type = db.Column(db.String(50), nullable=False)  # 'claim_received', 'claim_approved', 'claim_rejected', 'item_returned', 'message'
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    recipient = db.relationship("User", back_populates="notifications")
    related_item = db.relationship("Item", foreign_keys=[related_item_id])
    related_claim = db.relationship("Claim", foreign_keys=[related_claim_id])

    def __repr__(self) -> str:
        return f"<Notification id={self.id} recipient_id={self.recipient_id} title='{self.title}'>"
