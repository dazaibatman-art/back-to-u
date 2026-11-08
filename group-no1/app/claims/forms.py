from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class SubmitClaimForm(FlaskForm):
    """Ownership claim submission form."""
    claim_message = TextAreaField(
        "Claim Explanation *",
        validators=[
            DataRequired(message="Please explain how and where you lost this item."),
            Length(min=10, max=2000, message="Explanation must be between 10 and 2000 characters.")
        ]
    )
    evidence_details = TextAreaField(
        "Private Ownership Evidence *",
        validators=[
            DataRequired(message="Please provide confidential ownership evidence."),
            Length(min=5, max=3000, message="Evidence details must be between 5 and 3000 characters.")
        ]
    )
    submit = SubmitField("Submit Ownership Claim")


class ReviewClaimForm(FlaskForm):
    """Form for finder or admin to review ownership claim."""
    action = SelectField(
        "Decision *",
        choices=[
            ("Approved", "Approve Claim (Ownership Verified)"),
            ("Under Review", "Request More Information (Under Review)"),
            ("Rejected", "Reject Claim (Evidence Does Not Match)")
        ],
        validators=[DataRequired()]
    )
    review_notes = TextAreaField(
        "Review Notes & Response to Claimant",
        validators=[Optional(), Length(max=2000)]
    )
    submit = SubmitField("Submit Review")


class ClaimMessageForm(FlaskForm):
    """In-app communication message form."""
    content = TextAreaField(
        "Message",
        validators=[
            DataRequired(message="Message cannot be empty."),
            Length(min=1, max=1500)
        ]
    )
    submit = SubmitField("Send Message")
