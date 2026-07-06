"""
Tenant signals for automatic provisioning and cleanup.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Tenant, TenantUsage


@receiver(post_save, sender=Tenant)
def create_tenant_usage(sender, instance, created, **kwargs):
    if created:
        TenantUsage.objects.get_or_create(tenant=instance)


@receiver(post_delete, sender=Tenant)
def cleanup_tenant_schema(sender, instance, **kwargs):
    """Drop schema when tenant is deleted."""
    try:
        instance.drop_schema()
    except Exception:
        pass
