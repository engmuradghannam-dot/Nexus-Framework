from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ComplianceCheck


@receiver(post_save, sender=ComplianceCheck)
def handle_compliance_check(sender, instance, created, **kwargs):
    pass
