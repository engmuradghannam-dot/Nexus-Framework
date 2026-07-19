from django.utils import timezone


def generate_code(model, field_name, prefix, year=True, width=5):
    """Generate a sequential formatted code such as PRD-00001 or TRX-2026-00001.

    Looks at the highest existing code with the same prefix (and year, if
    applicable) and increments the numeric suffix.
    """
    pattern = f"{prefix}-{timezone.now().year}-" if year else f"{prefix}-"
    last = (
        model.objects.filter(**{f"{field_name}__startswith": pattern})
        .order_by(f"-{field_name}")
        .first()
    )
    last_seq = 0
    if last:
        last_value = getattr(last, field_name)
        try:
            last_seq = int(last_value.rsplit('-', 1)[-1])
        except (ValueError, AttributeError):
            last_seq = 0
    return f"{pattern}{str(last_seq + 1).zfill(width)}"
