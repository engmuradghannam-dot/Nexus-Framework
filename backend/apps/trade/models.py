"""Trade documents: quotations, delivery notes, goods receipts.

They tie the sales/purchase cycle to inventory (stock movements) and
accounting (invoices):
  - Goods Receipt  -> IN  stock movement  (feeds valuation)
  - Delivery Note  -> OUT stock movement  (reduces stock)
  - Quotation      -> converts to a sales Invoice
"""
from decimal import Decimal

from django.db import models


class TradeDoc(models.Model):
    TYPES = [
        ("quotation", "Quotation"),
        ("delivery", "Delivery Note"),
        ("receipt", "Goods Receipt"),
    ]
    STATUS = [("draft", "Draft"), ("posted", "Posted"), ("converted", "Converted")]

    doc_type = models.CharField(max_length=12, choices=TYPES, db_index=True)
    number = models.CharField(max_length=50, unique=True)
    party_name = models.CharField(max_length=200)
    date = models.DateField()
    item_code = models.CharField(max_length=50, blank=True)
    item_name = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    warehouse = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="draft", db_index=True)
    linked_ref = models.CharField(max_length=80, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trade_documents"
        ordering = ["-date", "-id"]

    @property
    def total(self):
        return Decimal(self.quantity or 0) * Decimal(self.unit_price or 0)

    def __str__(self):
        return f"{self.number} ({self.doc_type})"

    def process(self):
        """Post delivery/receipt to the stock ledger, or convert a quotation."""
        from apps.stockledger.models import StockMovement

        if self.status != "draft":
            return False, "تمّت معالجة المستند مسبقاً"

        if self.doc_type == "receipt":
            StockMovement.objects.create(
                item_code=self.item_code, item_name=self.item_name, warehouse=self.warehouse,
                movement_type="in", quantity=self.quantity, unit_cost=self.unit_price,
                date=self.date, reference=f"استلام {self.number}",
            )
            self.status = "posted"; self.linked_ref = f"STK-IN-{self.number}"; self.save()
            return True, "تم ترحيل الاستلام إلى المخزون"

        if self.doc_type == "delivery":
            StockMovement.objects.create(
                item_code=self.item_code, item_name=self.item_name, warehouse=self.warehouse,
                movement_type="out", quantity=self.quantity, unit_cost=self.unit_price,
                date=self.date, reference=f"تسليم {self.number}",
            )
            self.status = "posted"; self.linked_ref = f"STK-OUT-{self.number}"; self.save()
            return True, "تم ترحيل التسليم (خصم من المخزون)"

        if self.doc_type == "quotation":
            from apps.invoicing.models import Invoice
            inv = Invoice.objects.create(
                invoice_type="sales", invoice_number=f"SINV-{self.number}",
                party_name=self.party_name, invoice_date=self.date,
                subtotal=self.total, tax_rate=15,
            )
            self.status = "converted"; self.linked_ref = inv.invoice_number; self.save()
            return True, f"تم تحويل العرض إلى فاتورة {inv.invoice_number}"

        return False, "نوع غير مدعوم"
