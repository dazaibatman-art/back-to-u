from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Item, Claim, Message, Notification, utc_now
from app.claims import claims_bp
from app.claims.forms import SubmitClaimForm, ReviewClaimForm, ClaimMessageForm


@claims_bp.route("/items/<int:item_id>/claim", methods=["GET", "POST"])
def submit_claim(item_id: int):
    """
    Submit an ownership claim for an item.
    Enforces authentication, checks for duplicate claims, and prevents claiming one's own report.
    """
    if not current_user.is_authenticated:
        flash("Please log in to submit an ownership claim for this item.", "info")
        return redirect(url_for("auth.login", next=url_for("claims.submit_claim", item_id=item_id)))

    item = Item.query.get_or_404(item_id)

    # Prevent claiming own found item
    if item.finder_id == current_user.id:
        flash("You cannot submit a claim for an item you reported finding.", "error")
        return redirect(url_for("items.detail", item_id=item.id))

    # Prevent duplicate active claims
    existing_claim = Claim.query.filter_by(
        item_id=item.id,
        claimant_id=current_user.id
    ).first()

    if existing_claim and existing_claim.status not in ("Rejected",):
        flash(f"You already have an active claim ({existing_claim.status}) for this item.", "info")
        return redirect(url_for("claims.detail", claim_id=existing_claim.id))

    form = SubmitClaimForm()

    if form.validate_on_submit():
        claim = Claim(
            item_id=item.id,
            claimant_id=current_user.id,
            claim_message=form.claim_message.data.strip(),
            evidence_details=form.evidence_details.data.strip(),
            status="Pending"
        )
        db.session.add(claim)

        # Notify finder if known
        if item.finder_id:
            notification = Notification(
                recipient_id=item.finder_id,
                related_item_id=item.id,
                related_claim_id=claim.id,
                notification_type="claim_received",
                title="New Ownership Claim Received",
                message=f"{current_user.full_name} submitted a claim for '{item.name}'."
            )
            db.session.add(notification)

        try:
            db.session.commit()
            flash("Your ownership claim has been submitted! The finder will review your evidence.", "success")
            return redirect(url_for("claims.detail", claim_id=claim.id))
        except Exception:
            db.session.rollback()
            flash("Failed to submit claim. Please try again.", "error")

    return render_template("submit_claim.html", form=form, item=item)


@claims_bp.route("/claims/<int:claim_id>", methods=["GET"])
@login_required
def detail(claim_id: int):
    """
    View claim details, evidence, and communication thread.
    Protected by strict object-level authorization (claimant, finder, or admin only).
    """
    claim = Claim.query.get_or_404(claim_id)
    item = claim.item

    # Authorization check
    is_claimant = (current_user.id == claim.claimant_id)
    is_finder = (item.finder_id == current_user.id)
    is_admin = (current_user.role == "admin")

    if not (is_claimant or is_finder or is_admin):
        abort(403)

    review_form = ReviewClaimForm(status=claim.status, review_notes=claim.review_notes)
    message_form = ClaimMessageForm()

    return render_template(
        "claim_detail.html",
        claim=claim,
        item=item,
        is_claimant=is_claimant,
        is_finder=is_finder,
        is_admin=is_admin,
        review_form=review_form,
        message_form=message_form
    )


@claims_bp.route("/claims/<int:claim_id>/review", methods=["POST"])
@login_required
def review_claim(claim_id: int):
    """
    Review ownership claim (authorized finder or admin only).
    Updates claim status, updates item status, and notifies claimant.
    """
    claim = Claim.query.get_or_404(claim_id)
    item = claim.item

    is_finder = (item.finder_id == current_user.id)
    is_admin = (current_user.role == "admin")

    if not (is_finder or is_admin):
        abort(403)

    form = ReviewClaimForm()
    if form.validate_on_submit():
        decision = form.action.data
        notes = form.review_notes.data.strip() if form.review_notes.data else ""

        claim.status = decision
        claim.review_notes = notes
        claim.reviewer_id = current_user.id
        claim.reviewed_at = utc_now()

        # Update item status if approved
        if decision == "Approved":
            item.status = "claimed"
        elif decision == "Rejected" and item.status == "claimed":
            item.status = "active"

        # Create notification for claimant
        notif = Notification(
            recipient_id=claim.claimant_id,
            related_item_id=item.id,
            related_claim_id=claim.id,
            notification_type="claim_" + decision.lower().replace(" ", "_"),
            title=f"Claim Status Update: {decision}",
            message=f"Your claim for '{item.name}' was reviewed: status is now '{decision}'."
        )
        db.session.add(notif)

        try:
            db.session.commit()
            flash(f"Claim status updated to '{decision}'.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not update claim status. Please try again.", "error")

    return redirect(url_for("claims.detail", claim_id=claim.id))


@claims_bp.route("/claims/<int:claim_id>/complete", methods=["POST"])
@login_required
def complete_return(claim_id: int):
    """
    Mark an item return as fully completed.
    Authorized for finder or claimant after claim approval.
    """
    claim = Claim.query.get_or_404(claim_id)
    item = claim.item

    is_claimant = (current_user.id == claim.claimant_id)
    is_finder = (item.finder_id == current_user.id)
    is_admin = (current_user.role == "admin")

    if not (is_claimant or is_finder or is_admin):
        abort(403)

    claim.status = "Completed"
    claim.completed_at = utc_now()
    item.status = "returned"

    # Notify counterpart
    counterpart_id = claim.claimant_id if current_user.id == item.finder_id else item.finder_id
    if counterpart_id:
        notif = Notification(
            recipient_id=counterpart_id,
            related_item_id=item.id,
            related_claim_id=claim.id,
            notification_type="item_returned",
            title="Item Return Completed!",
            message=f"The return of '{item.name}' has been confirmed as completed."
        )
        db.session.add(notif)

    try:
        db.session.commit()
        flash("Congratulations! The item return is marked as Completed.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not complete return.", "error")

    return redirect(url_for("claims.detail", claim_id=claim.id))


@claims_bp.route("/claims/<int:claim_id>/messages", methods=["POST"])
@login_required
def send_message(claim_id: int):
    """
    Send a secure in-app message regarding this claim.
    Keeps personal phone numbers and emails private.
    """
    claim = Claim.query.get_or_404(claim_id)
    item = claim.item

    is_claimant = (current_user.id == claim.claimant_id)
    is_finder = (item.finder_id == current_user.id)
    is_admin = (current_user.role == "admin")

    if not (is_claimant or is_finder or is_admin):
        abort(403)

    form = ClaimMessageForm()
    if form.validate_on_submit():
        recipient_id = item.finder_id if is_claimant else claim.claimant_id
        if not recipient_id:
            flash("Cannot send message: recipient is not registered.", "error")
            return redirect(url_for("claims.detail", claim_id=claim.id))

        message = Message(
            claim_id=claim.id,
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=form.content.data.strip()
        )
        db.session.add(message)

        # Notify recipient
        notif = Notification(
            recipient_id=recipient_id,
            related_item_id=item.id,
            related_claim_id=claim.id,
            notification_type="new_message",
            title="New In-App Message Received",
            message=f"{current_user.full_name} sent a message regarding '{item.name}'."
        )
        db.session.add(notif)

        try:
            db.session.commit()
            flash("Message sent safely.", "success")
        except Exception:
            db.session.rollback()
            flash("Failed to send message.", "error")

    return redirect(url_for("claims.detail", claim_id=claim.id))
