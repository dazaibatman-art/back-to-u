from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models import User
from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm


def is_safe_url(target: str) -> bool:
    """Validate that redirect target is relative and safe from open redirect attacks."""
    if not target:
        return False
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ("", "http", "https") and (test_url.netloc == "" or test_url.netloc == ref_url.netloc)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user account with secure password hashing."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = User(
            full_name=form.full_name.data.strip(),
            email=normalized_email,
            phone=form.phone.data.strip() if form.phone.data else None
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        try:
            db.session.commit()
            login_user(user)
            flash("Account created successfully! Welcome to Group No1.", "success")
            return redirect(url_for("dashboard.index"))
        except Exception:
            db.session.rollback()
            flash("An unexpected error occurred while creating your account. Please try again.", "error")

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute")
def login():
    """User login with rate limiting and secure session authentication."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        normalized_email = form.email.data.strip().lower()
        user = User.query.filter_by(email=normalized_email).first()

        # Generic authentication error to prevent email enumeration attacks
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account has been deactivated. Please contact support.", "error")
                return render_template("login.html", form=form)

            login_user(user, remember=form.remember_me.data)
            flash("Login successful! Welcome back.", "success")
            
            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        else:
            flash("Invalid email or password. Please check your credentials.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Log the current user out and terminate session."""
    if current_user.is_authenticated:
        logout_user()
        flash("You have been successfully logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """View and update profile information."""
    profile_form = ProfileForm(obj=current_user)
    password_form = ChangePasswordForm()

    if "submit_profile" in request.form and profile_form.validate_on_submit():
        current_user.full_name = profile_form.full_name.data.strip()
        current_user.phone = profile_form.phone.data.strip() if profile_form.phone.data else None
        current_user.show_phone_publicly = profile_form.show_phone_publicly.data
        try:
            db.session.commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("auth.profile"))
        except Exception:
            db.session.rollback()
            flash("Could not update profile. Please try again.", "error")

    return render_template(
        "profile.html",
        user=current_user,
        profile_form=profile_form,
        password_form=password_form
    )


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change account password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("auth.profile"))

        current_user.set_password(form.new_password.data)
        try:
            db.session.commit()
            flash("Your password has been changed successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not update password. Please try again.", "error")

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Password error: {error}", "error")

    return redirect(url_for("auth.profile"))
