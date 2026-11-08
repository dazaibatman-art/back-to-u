from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, MultipleFileField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

CATEGORY_CHOICES = [
    ("", "Select Category"),
    ("electronics", "Electronics"),
    ("documents", "Documents"),
    ("accessories", "Accessories"),
    ("bags", "Bags"),
    ("jewelry", "Jewelry"),
    ("other", "Other"),
]

SEARCH_CATEGORY_CHOICES = [
    ("", "All Categories"),
    ("electronics", "Electronics"),
    ("documents", "Documents"),
    ("accessories", "Accessories"),
    ("bags", "Bags"),
    ("jewelry", "Jewelry"),
    ("other", "Other"),
]

STATUS_CHOICES = [
    ("", "All Statuses"),
    ("active", "Active"),
    ("pending_claim", "Pending Claim"),
    ("claimed", "Claimed"),
    ("returned", "Returned"),
]


class ReportItemForm(FlaskForm):
    """Form to report a found item."""
    name = StringField(
        "Item Name *",
        validators=[
            DataRequired(message="Item name is required."),
            Length(min=3, max=150, message="Item name must be between 3 and 150 characters.")
        ]
    )
    category = SelectField(
        "Category *",
        choices=CATEGORY_CHOICES,
        validators=[DataRequired(message="Please select a category.")]
    )
    public_description = TextAreaField(
        "Public Description *",
        validators=[
            DataRequired(message="Public description is required."),
            Length(min=10, max=2000, message="Description must be between 10 and 2000 characters.")
        ]
    )
    private_verification_details = TextAreaField(
        "Private Verification Details *",
        validators=[
            DataRequired(message="Private verification details are required."),
            Length(min=5, max=2000, message="Verification details must be between 5 and 2000 characters.")
        ]
    )
    location_found = StringField(
        "Location Found *",
        validators=[
            DataRequired(message="Location is required."),
            Length(min=2, max=200, message="Location must be between 2 and 200 characters.")
        ]
    )
    date_found = DateField(
        "Date Found *",
        default=date.today,
        validators=[DataRequired(message="Date found is required.")]
    )
    images = MultipleFileField("Upload Photos")
    submit = SubmitField("Submit Found Item")


class EditItemForm(FlaskForm):
    """Form to update existing found item report."""
    name = StringField(
        "Item Name *",
        validators=[DataRequired(), Length(min=3, max=150)]
    )
    category = SelectField(
        "Category *",
        choices=CATEGORY_CHOICES[1:],  # Exclude blank placeholder
        validators=[DataRequired()]
    )
    public_description = TextAreaField(
        "Public Description *",
        validators=[DataRequired(), Length(min=10, max=2000)]
    )
    private_verification_details = TextAreaField(
        "Private Verification Details *",
        validators=[DataRequired(), Length(min=5, max=2000)]
    )
    location_found = StringField(
        "Location Found *",
        validators=[DataRequired(), Length(min=2, max=200)]
    )
    date_found = DateField(
        "Date Found *",
        validators=[DataRequired()]
    )
    status = SelectField(
        "Status",
        choices=[
            ("active", "Active"),
            ("pending_claim", "Pending Claim"),
            ("claimed", "Claimed"),
            ("returned", "Returned"),
            ("archived", "Archived"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Update Item")
