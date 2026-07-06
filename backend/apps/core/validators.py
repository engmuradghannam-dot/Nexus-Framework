from django.core.exceptions import ValidationError

IMAGE_MAX_MB = 5
ATTACHMENT_MAX_MB = 10

ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']
ALLOWED_ATTACHMENT_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'docx', 'doc', 'csv']


def validate_image_size(file):
    """Rejects image uploads larger than IMAGE_MAX_MB megabytes."""
    max_bytes = IMAGE_MAX_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'Image too large. Maximum allowed size is {IMAGE_MAX_MB}MB.')


def validate_attachment_size(file):
    """Rejects generic attachment uploads larger than ATTACHMENT_MAX_MB megabytes."""
    max_bytes = ATTACHMENT_MAX_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(f'File too large. Maximum allowed size is {ATTACHMENT_MAX_MB}MB.')
