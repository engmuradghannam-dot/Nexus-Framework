from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import PurchaseOrderItem, PurchaseTaxCharge


@receiver(post_save, sender=PurchaseOrderItem)
@receiver(post_delete, sender=PurchaseOrderItem)
def recalc_on_item_change(sender, instance, **kwargs):
    instance.purchase_order.recalculate_totals()


@receiver(post_save, sender=PurchaseTaxCharge)
@receiver(post_delete, sender=PurchaseTaxCharge)
def recalc_on_tax_change(sender, instance, **kwargs):
    instance.purchase_order.recalculate_totals()
