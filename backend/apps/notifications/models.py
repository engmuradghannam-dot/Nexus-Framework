"""Email / SMS templates, message log, and a channel-agnostic send helper."""
import re

from django.db import models


class NotificationTemplate(models.Model):
    CHANNELS = [("email", "Email"), ("sms", "SMS")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    name = models.CharField(max_length=150)
    channel = models.CharField(max_length=5, choices=CHANNELS, default="email")
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(help_text="Use {placeholders} filled from context.")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_templates"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.channel})"

    def render(self, context):
        def sub(text):
            return re.sub(r"\{(\w+)\}", lambda m: str((context or {}).get(m.group(1), m.group(0))), text or "")
        return sub(self.subject), sub(self.body)


class NotificationLog(models.Model):
    STATUS = [("queued", "Queued"), ("sent", "Sent"), ("failed", "Failed")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    channel = models.CharField(max_length=5)
    recipient = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=STATUS, default="queued")
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_log"
        ordering = ["-created_at"]


def deliver(channel, recipient, subject, body, tenant=None):
    """Attempt delivery and record the outcome. Email uses Django's backend;
    SMS is queued (a real gateway can be wired in later). Never raises."""
    log = NotificationLog(tenant=tenant, channel=channel, recipient=recipient,
                          subject=subject, body=body, status="queued")
    if channel == "email":
        try:
            from django.conf import settings
            from django.core.mail import send_mail
            send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@nexus.app"),
                      [recipient], fail_silently=False)
            log.status = "sent"
        except Exception as exc:  # SMTP not configured in this env → queued
            log.status = "queued"
            log.error = str(exc)[:280]
    else:  # sms
        log.status = "queued"   # awaiting SMS gateway credentials
    log.save()
    return log
