"""Recording change documents (CDHDR/CDPOS) — field-level history.

The recorder captures the difference between two states of an object and writes
one header plus one item per changed field. Call snapshot() before a change and
record_change() after, or use record_create/record_delete for those operations.

Sensitive fields (salary, bank details) are tracked — you still get a row saying
the field changed, by whom and when — but their actual values are masked, so the
audit trail proves accountability without turning itself into a place private
numbers leak from.
"""
from django.contrib.contenttypes.models import ContentType

# Fields whose change is recorded, but whose values are masked in the trail.
SENSITIVE_FIELDS = {
    "salary", "basic_salary", "net_salary", "gross_salary", "wage",
    "iban", "bank_account", "account_number", "password", "national_id",
}

# Fields never worth recording — noise that would bury real changes.
IGNORED_FIELDS = {"updated_at", "created_at", "modified_at", "last_login"}

_MASK = "••••••"


def _display(field_name, value):
    if value is None:
        return None
    if field_name in SENSITIVE_FIELDS:
        return _MASK
    text = str(value)
    return text[:500]


def snapshot(instance, fields=None):
    """Capture an object's current field values, to diff against later."""
    if instance is None or instance.pk is None:
        return {}
    names = fields or [
        f.name for f in instance._meta.fields if f.name not in IGNORED_FIELDS
    ]
    snap = {}
    for name in names:
        try:
            snap[name] = getattr(instance, name)
        except Exception:
            continue
    return snap


def _diff(before, after):
    changed = {}
    for name, new_val in after.items():
        old_val = before.get(name)
        if old_val != new_val:
            changed[name] = (old_val, new_val)
    return changed


def _header(instance, operation, user=None, reason="", ip=None, tenant=None):
    from .models import ChangeDocument

    return ChangeDocument.objects.create(
        tenant=tenant,
        content_type=ContentType.objects.get_for_model(instance.__class__),
        object_id=str(instance.pk),
        object_repr=str(instance)[:200],
        operation=operation,
        user=user if (user and getattr(user, "is_authenticated", False)) else None,
        user_email=getattr(user, "email", "") or "",
        reason=reason[:200],
        ip_address=ip,
    )


def record_change(instance, before, user=None, reason="", ip=None, tenant=None):
    """Write a change document for the diff between `before` (a snapshot) and the
    instance's current state. No-op when nothing changed."""
    from .models import ChangeDocumentItem

    after = snapshot(instance, fields=list(before.keys()) or None)
    changed = _diff(before, after)
    if not changed:
        return None
    header = _header(instance, "update", user, reason, ip, tenant)
    ChangeDocumentItem.objects.bulk_create([
        ChangeDocumentItem(
            document=header, field_name=name,
            old_value=_display(name, old), new_value=_display(name, new),
        )
        for name, (old, new) in changed.items()
    ])
    return header


def record_create(instance, user=None, ip=None, tenant=None):
    """Record an object's creation, with its initial field values as items."""
    from .models import ChangeDocumentItem

    header = _header(instance, "create", user, "", ip, tenant)
    snap = snapshot(instance)
    ChangeDocumentItem.objects.bulk_create([
        ChangeDocumentItem(
            document=header, field_name=name,
            old_value=None, new_value=_display(name, val),
        )
        for name, val in snap.items() if val is not None
    ])
    return header


def record_delete(instance, user=None, ip=None, tenant=None):
    """Record an object's deletion, preserving its final field values."""
    from .models import ChangeDocumentItem

    snap = snapshot(instance)
    header = _header(instance, "delete", user, "", ip, tenant)
    ChangeDocumentItem.objects.bulk_create([
        ChangeDocumentItem(
            document=header, field_name=name,
            old_value=_display(name, val), new_value=None,
        )
        for name, val in snap.items() if val is not None
    ])
    return header
