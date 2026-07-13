"""Sales & purchase invoices that post real journal entries to the ledger."""
from decimal import Decimal

from django.db import models


class Invoice(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    company = models.ForeignKey(
        "core.CompanyProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invoices",
        help_text="Which company this invoice belongs to. Nullable for backward "
        "compatibility with rows created before this field existed; "
        "post_to_ledger() falls back to the oldest company if unset.",
    )
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

    @property
    def creditable_remaining(self):
        """Invoice total minus already-posted credit notes (for partial returns)."""
        from django.db.models import Sum
        if not self.pk:
            return Decimal(self.total or 0)
        posted = self.credit_notes.filter(status="posted").aggregate(s=Sum("total"))["s"] or Decimal(0)
        return Decimal(self.total or 0) - Decimal(posted)

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

        company = self.company or Company.objects.order_by("id").first()
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


class CreditNote(models.Model):
    """Credit note / return against a posted invoice.

    Sales invoice   -> sales return   (reverses: Dr Sales + Dr VAT, Cr A/R)
    Purchase invoice-> purchase return (reverses: Dr A/P, Cr Inventory + Cr VAT)

    Supports partial returns: the sum of posted credit notes for one invoice can
    never exceed that invoice's total. The reversal mirrors the original posting
    for the credited amount, keeping the ledger balanced.
    """

    STATUS = [("draft", "Draft"), ("posted", "Posted")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    company = models.ForeignKey("core.CompanyProfile", on_delete=models.CASCADE, null=True, blank=True, related_name="credit_notes")
    original_invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="credit_notes")
    credit_number = models.CharField(max_length=50, unique=True)
    credit_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=8, choices=STATUS, default="draft", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_notes"
        ordering = ["-credit_date", "-id"]

    def __str__(self):
        return f"{self.credit_number} -> {self.original_invoice.invoice_number}"

    @property
    def return_type(self):
        return "sales_return" if self.original_invoice.invoice_type == "sales" else "purchase_return"

    def recompute(self):
        self.total = Decimal(self.subtotal or 0) + Decimal(self.tax_amount or 0)

    def save(self, *args, **kwargs):
        self.recompute()
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.original_invoice_id and self.original_invoice.status != "posted":
            raise ValidationError("لا يمكن إصدار إشعار دائن إلا لفاتورة مُرحّلة.")
        self.recompute()
        if Decimal(self.total or 0) <= 0:
            raise ValidationError("قيمة الإشعار الدائن يجب أن تكون أكبر من صفر.")
        remaining = self.original_invoice.creditable_remaining if self.original_invoice_id else Decimal(0)
        # exclude self when editing an existing draft
        if self.pk:
            remaining += Decimal(self.total or 0) if self.status == "posted" else Decimal(0)
        if Decimal(self.total or 0) > remaining + Decimal("0.01"):
            raise ValidationError(
                f"القيمة ({self.total}) تتجاوز المبلغ القابل للإشعار ({remaining}) من الفاتورة.")

    def post_to_ledger(self):
        """Post the reversing journal entries. Idempotent + validated."""
        from apps.accounts.models import Account, JournalEntry
        from apps.core.models import Company

        if self.status == "posted":
            return False, "الإشعار الدائن مُرحّل مسبقاً"
        inv = self.original_invoice
        if inv.status != "posted":
            return False, "الفاتورة الأصلية غير مُرحّلة"

        self.recompute()
        if Decimal(self.total or 0) <= 0:
            return False, "قيمة غير صالحة"
        if Decimal(self.total or 0) > inv.creditable_remaining + Decimal("0.01"):
            return False, f"القيمة تتجاوز المبلغ القابل للإشعار ({inv.creditable_remaining})"

        company = self.company or inv.company or Company.objects.order_by("id").first()
        if company is None:
            return False, "لا توجد شركة"

        def acc(number):
            return Account.objects.filter(company=company, account_number=number).first()

        if inv.invoice_type == "sales":
            ar, rev, vat = acc("1300"), acc("4100"), acc("2200")
            if not all([ar, rev, vat]):
                return False, "حسابات المبيعات غير مهيأة"
            # reverse of (Dr AR / Cr Rev) and (Dr AR / Cr VAT)
            legs = [(rev, ar, self.subtotal), (vat, ar, self.tax_amount)]
        else:
            invacc, ap, vat = acc("1400"), acc("2100"), acc("2200")
            if not all([invacc, ap, vat]):
                return False, "حسابات المشتريات غير مهيأة"
            # reverse of (Dr Inventory / Cr AP) and (Dr VAT / Cr AP)
            legs = [(ap, invacc, self.subtotal), (ap, vat, self.tax_amount)]

        for i, (dr, cr, amt) in enumerate(legs):
            amt = Decimal(amt or 0)
            if amt <= 0:
                continue
            JournalEntry.objects.create(
                company=company,
                entry_number=f"CN-{self.credit_number}-{i+1}",
                posting_date=self.credit_date,
                reference=f"Credit Note {self.credit_number} (rev {inv.invoice_number})",
                debit_account=dr, credit_account=cr, amount=amt,
                total_debit=amt, total_credit=amt,
            )
            dr.post(debit_amount=amt)
            cr.post(credit_amount=amt)

        self.status = "posted"
        self.save(update_fields=["status"])
        return True, f"تم ترحيل الإشعار الدائن ({self.return_type})"
