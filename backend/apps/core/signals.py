from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Branch, Warehouse


@receiver(post_save, sender=Branch)
def create_default_warehouse(sender, instance, created, **kwargs):
    """BRN-RULE-001: every new branch gets a default warehouse.

    Without one, a branch can't receive or issue stock at all — and nothing in
    the UI creates a warehouse as part of branch setup.
    """
    if not created:
        return
    Warehouse.objects.create(
        branch=instance,
        name=f"{instance.name} - Main",
        code=f"{instance.code}-WH",
    )
