from django.core.management.base import BaseCommand

from apps.notifications.models import NotificationTemplate

DATA = [
    ("ترحيب بعميل", "email", "مرحباً بك في {company}", "عزيزي {name}،\nنشكر تعاملك معنا في {company}."),
    ("تذكير فاتورة", "email", "تذكير: فاتورة {invoice}", "عزيزي {name}، فاتورتكم {invoice} بقيمة {amount} ر.س مستحقة."),
    ("رمز التحقق", "sms", "", "رمز التحقق الخاص بك هو {code}."),
]


class Command(BaseCommand):
    help = "Seed sample notification templates (idempotent)."

    def handle(self, *args, **options):
        for name, ch, subj, body in DATA:
            NotificationTemplate.objects.get_or_create(name=name, defaults={"channel": ch, "subject": subj, "body": body})
        self.stdout.write(self.style.SUCCESS(f"Notification templates ensured: {NotificationTemplate.objects.count()}"))
