from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """User login form with CSRF protection."""
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email address."),
            Email(message="Please enter a valid email address.")
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter your password.")
        ]
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    """User registration form with email uniqueness validation."""
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=2, max=100, message="Full name must be between 2 and 100 characters.")
        ]
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email address is required."),
            Email(message="Please enter a valid email address."),
            Length(max=120, message="Email must not exceed 120 characters.")
        ]
    )
    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(min=7, max=25, message="Phone number should be between 7 and 25 digits/characters.")
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=6, max=128, message="Password must be at least 6 characters long.")
        ]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match.")
        ]
    )
    submit = SubmitField("Sign Up")

    def validate_email(self, field):
        """Ensure email is unique in the system."""
        normalized_email = field.data.strip().lower()
        if User.query.filter_by(email=normalized_email).first():
            raise ValidationError("This email address is already registered. Please log in.")


class ProfileForm(FlaskForm):
    """Profile editing form."""
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=2, max=100)
        ]
    )
    phone = StringField(
        "Phone Number",
        validators=[
            Optional(),
            Length(min=7, max=25)
        ]
    )
    show_phone_publicly = BooleanField("Allow claimants to see my phone number after claim approval")
    submit = SubmitField("Save Changes")


class ChangePasswordForm(FlaskForm):
    """Password update form."""
    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired(message="Please enter your current password.")]
    )
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Please enter a new password."),
            Length(min=6, max=128, message="Password must be at least 6 characters long.")
        ]
    )
    confirm_new_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo("new_password", message="Passwords must match.")
        ]
    )
    submit = SubmitField("Update Password")
