"""Generic audit trail — who changed what, and when."""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTIONS = [("create", "Created"), ("update", "Updated"), ("delete", "Deleted")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_logs",
    )
    user_email = models.CharField(max_length=254, blank=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    module = models.CharField(max_length=80, db_index=True)
    object_ref = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.action} {self.module}"


def record_audit(request, action, module, object_ref="", changes=None):
    """Helper to write an audit entry from a DRF view."""
    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        user = None
    ip = None
    if request is not None:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    AuditLog.objects.create(
        user=user,
        user_email=getattr(user, "email", "") or "",
        action=action,
        module=module,
        object_ref=str(object_ref)[:200],
        changes=changes or {},
        ip_address=ip or None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Change documents — the SAP CDHDR / CDPOS model.
#
# AuditLog above records that something happened, with the field changes bundled
# into one JSON blob. That's fine for a timeline but you can't ask it "who ever
# changed a salary?" — the changes aren't queryable. CDHDR/CDPOS splits the
# record in two: a header (ChangeDocument: who, when, which object, why) and one
# row per field changed (ChangeDocumentItem: field, old value, new value). The
# rows are real columns, so field-level history is queryable and auditable.
# ─────────────────────────────────────────────────────────────────────────────
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ChangeDocument(models.Model):
    """CDHDR — the header of one change event on one object."""

    OPERATIONS = [("create", "Created"), ("update", "Updated"), ("delete", "Deleted")]

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64, db_index=True)
    object_repr = models.CharField(max_length=200, blank=True)
    object = GenericForeignKey("content_type", "object_id")

    operation = models.CharField(max_length=10, choices=OPERATIONS)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="change_documents",
    )
    user_email = models.CharField(max_length=254, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "change_document"
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} {self.operation} {self.object_repr}"


class ChangeDocumentItem(models.Model):
    """CDPOS — one field's change within a ChangeDocument.

    Storing the field name and both values as columns is what makes field-level
    history queryable: 'every change to salary', 'who set status to posted', and
    so on — impossible when the diff lives in a JSON blob.
    """

    document = models.ForeignKey(
        ChangeDocument, on_delete=models.CASCADE, related_name="items"
    )
    field_name = models.CharField(max_length=100, db_index=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "change_document_item"
        ordering = ["document", "field_name"]
        indexes = [models.Index(fields=["field_name"])]

    def __str__(self):
        return f"{self.field_name}: {self.old_value} -> {self.new_value}"
