from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import SalesOrderItem, SalesTaxCharge


@receiver(post_save, sender=SalesOrderItem)
@receiver(post_delete, sender=SalesOrderItem)
def recalc_on_item_change(sender, instance, **kwargs):
    instance.sales_order.recalculate_totals()


@receiver(post_save, sender=SalesTaxCharge)
@receiver(post_delete, sender=SalesTaxCharge)
def recalc_on_tax_change(sender, instance, **kwargs):
    instance.sales_order.recalculate_totals()
