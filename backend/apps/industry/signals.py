from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import IndustryProject, IndustryMetric


@receiver(post_save, sender=IndustryProject)
def handle_project_save(sender, instance, created, **kwargs):
    if created:
        IndustryMetric.objects.get_or_create(
            project=instance,
            defaults={
                'efficiency_score': 0.0,
                'compliance_rate': 100.0,
                'risk_level': 'low'
            }
        )


@receiver(post_delete, sender=IndustryProject)
def handle_project_delete(sender, instance, **kwargs):
    IndustryMetric.objects.filter(project=instance).delete()
