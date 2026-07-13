"""Purchase cycle: RFQ -> Purchase Order -> Purchase Invoice (+ goods receipt)."""
from decimal import Decimal

from django.db import models


class PurchaseDoc(models.Model):
    TYPES = [("rfq", "RFQ"), ("po", "Purchase Order")]
    STATUS = [("draft", "Draft"), ("sent", "Sent"), ("converted", "Converted")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    doc_type = models.CharField(max_length=4, choices=TYPES, db_index=True)
    number = models.CharField(max_length=50, unique=True)
    supplier_name = models.CharField(max_length=200)
    date = models.DateField()
    item_code = models.CharField(max_length=50, blank=True)
    item_name = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    warehouse = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="draft", db_index=True)
    linked_ref = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "purchase_documents"
        ordering = ["-date", "-id"]

    @property
    def total(self):
        return Decimal(self.quantity or 0) * Decimal(self.unit_price or 0)

    def __str__(self):
        return f"{self.number} ({self.doc_type})"

    def _next_number(self, prefix):
        n = PurchaseDoc.objects.filter(number__startswith=prefix).count() + 1
        return f"{prefix}-{n:04d}"

    def process(self):
        """RFQ -> creates a PO. PO -> creates a purchase Invoice + goods receipt."""
        if self.status == "converted":
            return False, "تمّت المعالجة مسبقاً", None

        if self.doc_type == "rfq":
            po = PurchaseDoc.objects.create(
                tenant=self.tenant, doc_type="po", number=self._next_number("PO"),
                supplier_name=self.supplier_name, date=self.date, item_code=self.item_code,
                item_name=self.item_name, quantity=self.quantity, unit_price=self.unit_price,
                warehouse=self.warehouse, linked_ref=self.number,
            )
            self.status = "converted"; self.linked_ref = po.number; self.save()
            return True, f"تم تحويل طلب العرض إلى أمر شراء {po.number}", po.number

        if self.doc_type == "po":
            from apps.invoicing.models import Invoice
            from apps.stockledger.models import StockMovement
            inv = Invoice.objects.create(
                tenant=self.tenant, invoice_type="purchase",
                invoice_number=f"PINV-{self.number}", party_name=self.supplier_name,
                invoice_date=self.date, subtotal=self.total, tax_rate=15,
            )
            StockMovement.objects.create(
                tenant=self.tenant, item_code=self.item_code, item_name=self.item_name,
                warehouse=self.warehouse, movement_type="in", quantity=self.quantity,
                unit_cost=self.unit_price, date=self.date, reference=f"استلام {self.number}",
            )
            self.status = "converted"; self.linked_ref = inv.invoice_number; self.save()
            return True, f"تم إنشاء فاتورة شراء {inv.invoice_number} + استلام مخزني", inv.invoice_number

        return False, "نوع غير مدعوم", None
