from django.core.management.base import BaseCommand

from apps.automation.models import ScheduledJob, Webhook

JOBS = [
    ("تقرير المبيعات اليومي", "report", "daily"),
    ("تنبيه المخزون المنخفض", "notification", "hourly"),
    ("أرشفة السجلات القديمة", "cleanup", "monthly"),
]
HOOKS = [
    ("إشعار إنشاء فاتورة", "invoice.created", "https://example.com/hooks/invoice"),
    ("إشعار نقص مخزون", "stock.low", "https://example.com/hooks/stock"),
]


class Command(BaseCommand):
    help = "Seed sample scheduled jobs and webhooks (idempotent)."

    def handle(self, *args, **options):
        for name, jt, freq in JOBS:
            ScheduledJob.objects.get_or_create(name=name, defaults={"job_type": jt, "frequency": freq})
        for name, event, url in HOOKS:
            Webhook.objects.get_or_create(name=name, defaults={"event": event, "target_url": url})
        self.stdout.write(self.style.SUCCESS(f"Automation: {ScheduledJob.objects.count()} jobs, {Webhook.objects.count()} webhooks"))
