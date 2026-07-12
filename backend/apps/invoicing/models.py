"""Sales & purchase invoices that post real journal entries to the ledger."""
from decimal import Decimal

from django.db import models


class Invoice(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    TYPES = [("sales", "Sales"), ("purchase", "Purchase")]
    STATUS = [("draft", "Draft"), ("posted", "Posted"), ("cancelled", "Cancelled")]

    invoice_type = models.CharField(max_length=10, choices=TYPES, db_index=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    party_name = models.CharField(max_length=200)
    invoice_date = models.DateField()
    currency = models.CharField(max_length=10, default="SAR")
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    zatca_category = models.CharField(max_length=1, default="S", blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="draft", db_index=True)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-invoice_date", "-id"]

    def __str__(self):
        return f"{self.invoice_number} ({self.invoice_type})"

    @property
    def outstanding(self):
        from decimal import Decimal
        return Decimal(self.total or 0) - Decimal(self.paid_amount or 0)

    def recompute(self):
        sub = Decimal(self.subtotal or 0)
        self.tax_amount = (sub * Decimal(self.tax_rate or 0) / Decimal(100)).quantize(Decimal("0.01"))
        self.total = sub + self.tax_amount

    def save(self, *args, **kwargs):
        self.recompute()
        if not self.due_date and self.invoice_date:
            from datetime import timedelta
            self.due_date = self.invoice_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def post_to_ledger(self):
        """Create balanced double-entry journal entries for this invoice.

        Sales:    Dr A/R (total)         Cr Sales (subtotal) + Cr VAT (tax)
        Purchase: Dr Inventory (subtotal) + Dr VAT (tax)   Cr A/P (total)
        Implemented as two single debit/credit entries so it stays balanced.
        """
        from apps.accounts.models import Account, JournalEntry
        from apps.core.models import Company

        if self.status == "posted":
            return False, "الفاتورة مرحّلة مسبقاً"

        company = Company.objects.order_by("id").first()
        if company is None:
            return False, "لا توجد شركة"

        def acc(number):
            return Account.objects.filter(company=company, account_number=number).first()

        if self.invoice_type == "sales":
            ar, rev, vat = acc("1300"), acc("4100"), acc("2200")
            if not all([ar, rev, vat]):
                return False, "حسابات المبيعات غير مهيأة — شغّل seed_accounting"
            legs = [(ar, rev, self.subtotal), (ar, vat, self.tax_amount)]
        else:
            inv, ap, vat = acc("1400"), acc("2100"), acc("2200")
            if not all([inv, ap, vat]):
                return False, "حسابات المشتريات غير مهيأة — شغّل seed_accounting"
            legs = [(inv, ap, self.subtotal), (vat, ap, self.tax_amount)]

        base = JournalEntry.objects.count() + 1
        for i, (dr, cr, amt) in enumerate(legs):
            amt = Decimal(amt or 0)
            if amt <= 0:
                continue
            JournalEntry.objects.create(
                company=company,
                entry_number=f"INV-{self.invoice_number}-{i+1}",
                posting_date=self.invoice_date,
                reference=f"{self.get_invoice_type_display()} Invoice {self.invoice_number}",
                debit_account=dr, credit_account=cr, amount=amt,
                total_debit=amt, total_credit=amt,
            )
            dr.post(debit_amount=amt)
            cr.post(credit_amount=amt)

        self.status = "posted"
        self.save(update_fields=["status"])
        return True, "تم الترحيل إلى دفتر الأستاذ"
