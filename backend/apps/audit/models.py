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
