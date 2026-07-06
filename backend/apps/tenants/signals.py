"""
Tenant signals for django-tenants integration.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_tenants.utils import schema_context
from .models import Tenant, TenantUsage


@receiver(post_save, sender=Tenant)
def create_tenant_usage(sender, instance, created, **kwargs):
    if created:
        TenantUsage.objects.get_or_create(tenant=instance)


@receiver(post_save, sender=Tenant)
def create_company_in_tenant_schema(sender, instance, created, **kwargs):
    """Create Company record in tenant schema when tenant is created."""
    if created:
        with schema_context(instance.schema_name):
            from apps.core.models import Company
            Company.objects.get_or_create(
                name=instance.name,
                defaults={
                    'email': instance.email,
                    'phone': instance.phone,
                    'address': instance.address,
                    'country': instance.country,
                    'timezone': instance.timezone,
                }
            )
