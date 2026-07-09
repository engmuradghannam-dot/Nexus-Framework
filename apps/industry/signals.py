from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import IndustryProject, IndustryMetric


@receiver(post_save, sender=IndustryProject)
def update_project_metrics(sender, instance, created, **kwargs):
    """Update metrics when project changes"""
    if created:
        # Create default metrics for new project
        IndustryMetric.objects.create(
            project=instance,
            name='Progress',
            value=0.0,
            target=100.0,
            unit='percent'
        )


@receiver(post_delete, sender=IndustryProject)
def cleanup_project_metrics(sender, instance, **kwargs):
    """Cleanup related metrics when project is deleted"""
    pass  # Cascade delete handles this automatically
