"""
Billing signals for automatic invoice generation and limit enforcement.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subscription, Invoice


@receiver(post_save, sender=Subscription)
def create_initial_invoice(sender, instance, created, **kwargs):
    """Generate initial invoice on subscription creation."""
    if created:
        from django.utils import timezone
        import uuid
        Invoice.objects.create(
            tenant=instance.tenant,
            subscription=instance,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            status='draft',
            subtotal=instance.plan.get_price(),
            currency=instance.plan.currency,
            due_date=instance.current_period_end,
        )
