"""Scheduled jobs and outgoing webhooks (tenant-scoped)."""
import json
from datetime import timedelta

from django.db import models
from django.utils import timezone


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
    target_url = models.URLField(max_length=500)
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
