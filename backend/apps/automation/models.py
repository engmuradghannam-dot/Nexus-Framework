"""Scheduled jobs and outgoing webhooks (tenant-scoped)."""
import ipaddress
import json
import socket
from datetime import timedelta
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_webhook_target_url(url):
    """Block SSRF: reject webhook targets that resolve to loopback,
    link-local (incl. cloud metadata 169.254.169.254), private, or
    otherwise non-public IP ranges."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValidationError("Webhook target_url must be http:// or https://.")
    hostname = parts.hostname
    if not hostname:
        raise ValidationError("Webhook target_url must include a host.")
    try:
        addrs = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
    except socket.gaierror as exc:
        raise ValidationError(f"Could not resolve webhook host: {exc}") from exc
    for addr in addrs:
        ip = ipaddress.ip_address(addr)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValidationError(
                f"Webhook target_url resolves to a non-public address ({addr}) — not allowed."
            )


class ScheduledJob(models.Model):
    FREQ = [("hourly", "Hourly"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]
    JOB_TYPES = [("report", "Report"), ("notification", "Notification"), ("cleanup", "Cleanup"), ("sync", "Sync"), ("custom", "Custom")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    name = models.CharField(max_length=150)
    job_type = models.CharField(max_length=15, choices=JOB_TYPES, default="custom")
    frequency = models.CharField(max_length=10, choices=FREQ, default="daily")
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    run_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scheduled_jobs"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def next_run(self):
        base = self.last_run or self.created_at or timezone.now()
        delta = {"hourly": timedelta(hours=1), "daily": timedelta(days=1),
                 "weekly": timedelta(weeks=1), "monthly": timedelta(days=30)}[self.frequency]
        return base + delta

    def run_now(self):
        self.last_run = timezone.now()
        self.run_count += 1
        self.save(update_fields=["last_run", "run_count"])
        return f"تم تشغيل المهمة «{self.name}» (تشغيل رقم {self.run_count})"


class Webhook(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    name = models.CharField(max_length=150)
    event = models.CharField(max_length=80, help_text="e.g. invoice.created, stock.low")
    target_url = models.URLField(max_length=500, validators=[validate_webhook_target_url])
    secret = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhooks"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} -> {self.event}"

    def deliver(self, payload=None):
        """POST the payload to the target URL and log the delivery. Never raises."""
        import urllib.request

        body = json.dumps(payload or {"event": self.event, "ts": timezone.now().isoformat()}).encode()
        delivery = WebhookDelivery(webhook=self, tenant=self.tenant, event=self.event,
                                   payload=payload or {})
        try:
            # Re-validate at delivery time (defense in depth): the row may
            # predate this check, and DNS can rebind between create and send.
            validate_webhook_target_url(self.target_url)
            req = urllib.request.Request(self.target_url, data=body,
                                         headers={"Content-Type": "application/json",
                                                  "X-Webhook-Secret": self.secret})
            with urllib.request.urlopen(req, timeout=8) as resp:
                delivery.status = "success"
                delivery.status_code = resp.status
        except Exception as exc:
            delivery.status = "failed"
            delivery.error = str(exc)[:280]
        delivery.save()
        return delivery


class WebhookDelivery(models.Model):
    STATUS = [("pending", "Pending"), ("success", "Success"), ("failed", "Failed")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name="deliveries")
    event = models.CharField(max_length=80)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=8, choices=STATUS, default="pending")
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_deliveries"
        ordering = ["-created_at"]


class AutomatedAction(models.Model):
    """A rule: on an event, if a condition holds, do something — no code.

    Modelled on Odoo's automated actions. When a document of `model_label` fires
    `trigger` (created, updated, or a field reaching a value), and the optional
    condition passes, each of the action's steps runs — set a field, send a
    notification, or fire a webhook. The condition is evaluated by a safe
    comparator, never eval(); it can only read the record's own fields.
    """

    TRIGGERS = [
        ("on_create", "On create"),
        ("on_update", "On update"),
        ("on_create_or_update", "On create or update"),
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=150)
    model_label = models.CharField(
        max_length=80, db_index=True,
        help_text="Which model this watches, as 'app_label.ModelName'.",
    )
    trigger = models.CharField(max_length=20, choices=TRIGGERS, default="on_create")

    # Optional condition: "<field> <op> <value>", e.g. "total > 10000".
    condition_field = models.CharField(max_length=60, blank=True)
    condition_operator = models.CharField(
        max_length=4, blank=True,
        help_text="One of ==, !=, >, >=, <, <=.",
    )
    condition_value = models.CharField(max_length=120, blank=True)

    is_active = models.BooleanField(default=True)
    run_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automated_actions"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def condition_holds(self, instance):
        """Whether this rule's condition passes for `instance`. No condition
        means it always passes."""
        if not self.condition_field or not self.condition_operator:
            return True
        from .actions import compare

        actual = getattr(instance, self.condition_field, None)
        return compare(actual, self.condition_operator, self.condition_value)

    def run_on(self, instance, actor=None):
        """Run every step against `instance`. Returns the list of results."""
        results = []
        for step in self.steps.filter(is_active=True).order_by("order"):
            results.append(step.execute(instance, actor=actor))
        AutomatedAction.objects.filter(pk=self.pk).update(run_count=self.run_count + 1)
        return results


class AutomatedActionStep(models.Model):
    """One thing an automated action does when it fires."""

    STEP_TYPES = [
        ("set_field", "Set a field"),
        ("notify", "Create a notification"),
        ("webhook", "Fire a webhook"),
    ]

    action = models.ForeignKey(
        AutomatedAction, on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveSmallIntegerField(default=0)
    step_type = models.CharField(max_length=10, choices=STEP_TYPES)

    # set_field
    target_field = models.CharField(max_length=60, blank=True)
    target_value = models.CharField(max_length=200, blank=True)
    # notify
    message = models.CharField(max_length=300, blank=True)
    # webhook
    webhook = models.ForeignKey(
        Webhook, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "automated_action_steps"
        ordering = ["action", "order"]

    def __str__(self):
        return f"{self.action.name} → {self.step_type}"

    def execute(self, instance, actor=None):
        from .actions import run_step

        return run_step(self, instance, actor=actor)
