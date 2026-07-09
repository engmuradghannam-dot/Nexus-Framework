"""Core validators for the Nexus Framework."""
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']


def validate_image_size(image):
    """Validate image file size (max 5MB)."""
    file_size = image.size
    limit_mb = 5
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max file size is {limit_mb}MB")


def validate_attachment_size(attachment):
    """Validate attachment file size (max 10MB)."""
    file_size = attachment.size
    limit_mb = 10
    if file_size > limit_mb * 1024 * 1024:
        raise ValidationError(f"Max file size is {limit_mb}MB")
