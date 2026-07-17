from django.db.models import QuerySet
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Invoice, InvoiceItem


def _origin_is_the_invoice(origin):
    """True when the deletion cascaded down from the parent Invoice itself.

    Django passes the object (or queryset) the delete originated from as
    ``origin``. When the Invoice is what's being deleted, recalculating its
    totals from the child rows is pointless work against a row that is about to
    disappear — and issues an UPDATE mid-cascade.
    """
    if isinstance(origin, Invoice):
        return True
    return isinstance(origin, QuerySet) and origin.model is Invoice


@receiver(post_save, sender=InvoiceItem)
def recalc_on_item_save(sender, instance, **kwargs):
    instance.invoice.recalculate_totals()


@receiver(post_delete, sender=InvoiceItem)
def recalc_on_item_delete(sender, instance, origin=None, **kwargs):
    if _origin_is_the_invoice(origin):
        return
    if not Invoice.objects.filter(pk=instance.invoice_id).exists():
        return
    # force=True: removing the last line must zero the totals rather than leave
    # the invoice stranded at its previous amount.
    instance.invoice.recalculate_totals(force=True)
