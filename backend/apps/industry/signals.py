from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Company, Metric


@receiver(post_save, sender=Company)
def handle_company_save(sender, instance, created, **kwargs):
    """Auto-create default metrics when a new company is created."""
    if created:
        Metric.objects.get_or_create(
            company=instance,
            name="Default Efficiency",
            defaults={
                "metric_type": "operational",
                "value": 0.0,
                "unit": "score",
                "period": "initial",
            },
        )


@receiver(post_delete, sender=Company)
def handle_company_delete(sender, instance, **kwargs):
    """Clean up metrics when a company is deleted."""
    Metric.objects.filter(company=instance).delete()
