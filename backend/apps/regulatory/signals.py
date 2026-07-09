from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ComplianceRule, AuditLog


@receiver(post_save, sender=ComplianceRule)
def handle_rule_change(sender, instance, created, **kwargs):
    if not created:
        AuditLog.objects.create(
            rule=instance,
            action='updated',
            details=f'Rule {instance.name} was modified'
        )
