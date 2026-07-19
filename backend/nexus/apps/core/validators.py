"""Shared field-level validators, reused across every module to enforce the
Validation Rule column of the ERP data spec (alphanumeric codes, letters-only
names, phone formats, strictly-positive numbers, etc.)."""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

alphanumeric_validator = RegexValidator(
    regex=r'^[A-Za-z0-9]+$',
    message='This field must contain only letters and numbers (no spaces or symbols).',
)

# Unicode-aware "letters only" (also allows spaces/hyphens/apostrophes for
# compound names) so Arabic and other non-ASCII names remain valid.
letters_only_validator = RegexValidator(
    regex=r"^[^\W\d_][^\d_]*$",
    message='This field must contain letters only.',
)

phone_validator = RegexValidator(
    regex=r'^\+?[0-9\-\s()]{7,20}$',
    message='Enter a valid phone number.',
)


def positive_validator(value):
    """Ensure this value is strictly greater than 0.

    Deliberately a plain function rather than a MinValueValidator subclass:
    DRF's ModelSerializer introspects model field validators and, for any
    isinstance(v, MinValueValidator)/MaxValueValidator, replaces it with its
    own *inclusive* min_value/max_value handling - silently discarding a
    subclassed "exclusive" compare() override. A plain callable is passed
    through untouched.
    """
    if value is not None and value <= 0:
        raise ValidationError('Ensure this value is greater than 0.', code='min_value')
