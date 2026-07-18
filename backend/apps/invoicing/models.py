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
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=6, default=1, help_text="Rate to base currency at invoice date")
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    zatca_category = models.CharField(max_length=1, default="S", blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="draft", db_index=True)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    discount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Document-level discount, subtracted from subtotal before arriving at "
        "total. Mirrors SalesOrder.discount / PurchaseOrder.discount so an order converts "
        "to an invoice without silently dropping the discount the customer was quoted.",
    )
    branch = models.ForeignKey(
        "core.Branch", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices",
        help_text="BRN-CTRL-004: which branch this invoice's revenue/expense "
        "belongs to. Invoices carried no branch at all, so nothing a branch "
        "earned could be attributed back to it.",
    )
    cost_center = models.ForeignKey(
        "accounts.CostCenter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", help_text="Cost center this invoice's revenue/expense is attributed to.",
    )
    project = models.ForeignKey(
        "pmo.Project", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", help_text="Project this invoice bills against, if any.",
    )
    against_sales_order = models.ForeignKey(
        "selling.SalesOrder", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", help_text="Sales Order this invoice was generated from, if any.",
    )
    against_purchase_order = models.ForeignKey(
        "buying.PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoices", help_text="Purchase Order this invoice was generated from, if any.",
    )
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

    @property
    def is_fully_paid(self):
        return self.outstanding <= Decimal("0.01")

    @property
    def base_total(self):
        return (Decimal(self.total or 0) * Decimal(self.exchange_rate or 1)).quantize(Decimal("0.01"))

    @property
    def is_foreign(self):
        return Decimal(self.exchange_rate or 1) != Decimal(1)

    def sync_paid_amount(self):
        """Recompute paid_amount from the posted payment log (source of truth)."""
        from django.db.models import Sum
        total_paid = self.payments.filter(posted=True).aggregate(s=Sum("amount"))["s"] or Decimal(0)
        self.paid_amount = total_paid
        self.save(update_fields=["paid_amount"])
        return self.paid_amount

    def has_line_items(self):
        """Whether this invoice carries item-level detail. Invoices entered as a
        flat subtotal (the only option before InvoiceItem existed) have none."""
        return bool(self.pk) and self.line_items.exists()

    def recompute(self):
        """Derive tax/total from the flat subtotal + document tax_rate.

        Only meaningful for flat-entry invoices. Once line items exist they own
        the totals, and recomputing from subtotal * tax_rate here would silently
        clobber the per-line VAT on the next save() — so bail out instead.
        """
        if self.has_line_items():
            return
        sub = Decimal(self.subtotal or 0)
        self.tax_amount = (sub * Decimal(self.tax_rate or 0) / Decimal(100)).quantize(Decimal("0.01"))
        self.total = sub - Decimal(self.discount or 0) + self.tax_amount

    def recalculate_totals(self, force=False):
        """Recompute subtotal/tax_amount/total from line items.

        Called via the InvoiceItem post_save/post_delete signal (mirrors
        SalesOrder.recalculate_totals / PurchaseOrder.recalculate_totals).

        With no line items this is a no-op by default, so legacy flat-entry
        invoices keep working. ``force=True`` (used by post_delete) zeroes the
        totals instead, so removing the last line doesn't strand the invoice at
        its old amount.
        """
        items = list(self.line_items.all())
        if not items and not force:
            return
        subtotal = sum((i.amount for i in items), Decimal(0))
        tax_amount = sum((i.tax_amount for i in items), Decimal(0))
        total = subtotal - Decimal(self.discount or 0) + tax_amount
        self.subtotal, self.tax_amount, self.total = subtotal, tax_amount, total
        Invoice.objects.filter(pk=self.pk).update(
            subtotal=subtotal, tax_amount=tax_amount, total=total
        )

    @staticmethod
    def _effective_tax_rate(order):
        """Collapse an order's document-level tax charges to a single rate.

        SalesOrder/PurchaseOrder model VAT as SalesTaxCharge/PurchaseTaxCharge
        rows against the whole document, not per line — so there is no per-line
        rate to copy. Deriving the effective rate (total_tax / total_amount)
        keeps the generated invoice's VAT equal to the order's own, which taking
        the *first* charge's rate would not once a document carries more than
        one charge.
        """
        total_amount = Decimal(order.total_amount or 0)
        total_tax = Decimal(order.total_tax or 0)
        if total_amount <= 0 or total_tax <= 0:
            return Decimal(0)
        return (total_tax / total_amount * Decimal(100)).quantize(Decimal("0.0001"))

    @classmethod
    def _create_from_order(cls, order, *, invoice_type, party_name, order_field,
                           invoice_number, invoice_date, due_date=None):
        from django.core.exceptions import ValidationError
        from django.db import transaction
        from django.utils.dateparse import parse_date

        def as_date(value, field):
            # Invoice.save() does arithmetic on invoice_date to default due_date,
            # so a raw "YYYY-MM-DD" string off the API blows up there instead of
            # here. Normalise at the door.
            if value is None or not isinstance(value, str):
                return value
            parsed = parse_date(value)
            if parsed is None:
                raise ValidationError(f"{field} must be a valid date (YYYY-MM-DD).")
            return parsed

        invoice_date = as_date(invoice_date, "invoice_date")
        due_date = as_date(due_date, "due_date")

        if order.status not in ("Submitted", "Delivered", "Received"):
            raise ValidationError(
                f"Cannot invoice an order in status '{order.status}' — submit it first."
            )
        if not order.items.exists():
            raise ValidationError("Cannot invoice an order with no line items.")
        if cls.objects.filter(invoice_number=invoice_number).exists():
            raise ValidationError(f"Invoice number '{invoice_number}' already exists.")

        rate = cls._effective_tax_rate(order)
        with transaction.atomic():
            inv = cls.objects.create(
                company=order.company,
                invoice_type=invoice_type,
                invoice_number=invoice_number,
                party_name=party_name,
                invoice_date=invoice_date,
                due_date=due_date,
                currency=order.currency,
                # Invoice.tax_rate is 2dp and purely informational once line items
                # exist (recompute() defers to them); the lines keep full precision.
                tax_rate=rate.quantize(Decimal("0.01")),
                discount=order.discount or Decimal(0),
                branch=getattr(order, "branch", None),
                cost_center=getattr(order, "cost_center", None),
                project=getattr(order, "project", None),
                **{order_field: order},
            )
            for line in order.items.all():
                InvoiceItem.objects.create(
                    invoice=inv, item=line.item, qty=line.qty, rate=line.rate, tax_rate=rate,
                )
            inv.refresh_from_db()
            inv.recalculate_totals()
            order.__class__.objects.filter(pk=order.pk).update(
                billed_amount=models.F("billed_amount") + inv.total
            )
        return inv

    @classmethod
    def create_from_sales_order(cls, sales_order, invoice_number, invoice_date, due_date=None):
        """Build a draft Sales Invoice from a submitted Sales Order, copying every
        line item across so item-level detail survives into the ZATCA-facing
        document instead of being re-typed by hand."""
        return cls._create_from_order(
            sales_order, invoice_type="sales", party_name=sales_order.customer.name,
            order_field="against_sales_order", invoice_number=invoice_number,
            invoice_date=invoice_date, due_date=due_date,
        )

    @classmethod
    def create_from_purchase_order(cls, purchase_order, invoice_number, invoice_date, due_date=None):
        """Build a draft Purchase Invoice from a submitted Purchase Order
        (see create_from_sales_order)."""
        return cls._create_from_order(
            purchase_order, invoice_type="purchase", party_name=purchase_order.supplier.name,
            order_field="against_purchase_order", invoice_number=invoice_number,
            invoice_date=invoice_date, due_date=due_date,
        )

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
        from apps.accounts.models import Account, AccountingPeriod, JournalEntry
        from apps.core.models import Company

        if self.status == "posted":
            return False, "الفاتورة مرحّلة مسبقاً"

        company = self.company or Company.objects.order_by("id").first()
        if company is None:
            return False, "لا توجد شركة"

        if AccountingPeriod.is_locked(company, self.invoice_date):
            return False, "الفترة المحاسبية مقفلة لهذا التاريخ"
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
            amt = Decimal(amt or 0) * Decimal(self.exchange_rate or 1)
            if amt <= 0:
                continue
            JournalEntry.objects.create(
                company=company,
                branch=self.branch,
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

    def void(self):
        """Cancel a posted invoice by reversing its ledger posting.

        Guards: only a posted invoice; no recorded payments; no posted credit
        notes (those must be handled first). Creates balanced reversing entries
        and sets the invoice to cancelled.
        """
        from apps.accounts.models import Account, AccountingPeriod, JournalEntry
        from apps.core.models import Company

        if self.status != "posted":
            return False, "لا يمكن إلغاء إلا فاتورة مُرحّلة"
        if Decimal(self.paid_amount or 0) > 0:
            return False, "لا يمكن إلغاء فاتورة عليها دفعات مُسجّلة — عالج الدفعات أولاً"
        if self.pk and self.credit_notes.filter(status="posted").exists():
            return False, "لا يمكن إلغاء فاتورة لها إشعارات دائنة مُرحّلة"

        company = self.company or Company.objects.order_by("id").first()
        if company is None:
            return False, "لا توجد شركة"

        if AccountingPeriod.is_locked(company, self.invoice_date):
            return False, "الفترة المحاسبية مقفلة لهذا التاريخ"
        def acc(number):
            return Account.objects.filter(company=company, account_number=number).first()

        if self.invoice_type == "sales":
            ar, rev, vat = acc("1300"), acc("4100"), acc("2200")
            if not all([ar, rev, vat]):
                return False, "حسابات المبيعات غير مهيأة"
            legs = [(rev, ar, self.subtotal), (vat, ar, self.tax_amount)]
        else:
            invacc, ap, vat = acc("1400"), acc("2100"), acc("2200")
            if not all([invacc, ap, vat]):
                return False, "حسابات المشتريات غير مهيأة"
            legs = [(ap, invacc, self.subtotal), (ap, vat, self.tax_amount)]

        for i, (dr, cr, amt) in enumerate(legs):
            amt = Decimal(amt or 0) * Decimal(self.exchange_rate or 1)
            if amt <= 0:
                continue
            JournalEntry.objects.create(
                company=company,
                branch=self.branch,
                entry_number=f"VOID-{self.invoice_number}-{i+1}",
                posting_date=self.invoice_date,
                reference=f"Void {self.get_invoice_type_display()} Invoice {self.invoice_number}",
                debit_account=dr, credit_account=cr, amount=amt,
                total_debit=amt, total_credit=amt,
            )
            dr.post(debit_amount=amt)
            cr.post(credit_amount=amt)

        self.status = "cancelled"
        self.save(update_fields=["status"])
        return True, "تم إلغاء الفاتورة وعكس ترحيلها المحاسبي"


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
        from apps.accounts.models import Account, AccountingPeriod, JournalEntry
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

        if AccountingPeriod.is_locked(company, self.credit_date):
            return False, "الفترة المحاسبية مقفلة لهذا التاريخ"
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
            amt = Decimal(amt or 0) * Decimal(inv.exchange_rate or 1)
            if amt <= 0:
                continue
            JournalEntry.objects.create(
                company=company,
                branch=self.original_invoice.branch,
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


class Payment(models.Model):
    """A single payment against an invoice — full audit trail for partial pays.

    Sales receipt:  Dr Cash/Bank, Cr A/R
    Purchase pay:   Dr A/P,       Cr Cash/Bank
    The cash vs bank account is chosen by the payment method.
    """

    METHODS = [("cash", "Cash"), ("bank", "Bank Transfer"), ("card", "Card"),
               ("cheque", "Cheque")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=8, choices=METHODS, default="bank")
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=6, default=1, help_text="Rate to base currency at payment date")
    reference = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    posted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_payments"
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"{self.amount} on {self.invoice.invoice_number}"

    def post_to_ledger(self):
        """Validate, post the cash/AR (or AP/cash) entry, and sync the invoice."""
        from apps.accounts.models import Account, AccountingPeriod, JournalEntry
        from apps.core.models import Company

        if self.posted:
            return False, "الدفعة مُرحّلة مسبقاً"
        inv = self.invoice
        if inv.status != "posted":
            return False, "لا يمكن تسجيل دفعة إلا لفاتورة مُرحّلة"
        amt = Decimal(self.amount or 0)
        if amt <= 0:
            return False, "مبلغ غير صالح"
        if amt > inv.outstanding + Decimal("0.01"):
            return False, f"المبلغ ({amt}) يتجاوز المتبقّي ({inv.outstanding})"

        company = self.company_or_default()
        if company is None:
            return False, "لا توجد شركة"

        if AccountingPeriod.is_locked(company, self.payment_date):
            return False, "الفترة المحاسبية مقفلة لهذا التاريخ"
        def acc(number):
            return Account.objects.filter(company=company, account_number=number).first()

        cash = acc("1100") if self.method == "cash" else acc("1200")
        ar, ap = acc("1300"), acc("2100")
        if inv.invoice_type == "sales":
            if not all([cash, ar]):
                return False, "حسابات النقد/المدينون غير مهيأة"
            dr, cr = cash, ar
        else:
            if not all([cash, ap]):
                return False, "حسابات النقد/الدائنون غير مهيأة"
            dr, cr = ap, cash

        n = inv.payments.filter(posted=True).count() + 1
        pay_rate = Decimal(self.exchange_rate or 1)
        inv_rate = Decimal(inv.exchange_rate or 1)
        base_cash = (amt * pay_rate).quantize(Decimal("0.01"))       # actual base cash moved
        base_relieved = (amt * inv_rate).quantize(Decimal("0.01"))   # AR/AP relieved at invoice rate
        fx_gain, fx_loss = acc("4900"), acc("5900")
        ref = f"Payment {inv.invoice_number} ({self.get_method_display()})"

        def je(d, c, base_amt, suffix=""):
            JournalEntry.objects.create(
                company=company,
                branch=inv.branch, entry_number=f"PAY-{inv.invoice_number}-{n}{suffix}",
                posting_date=self.payment_date, reference=ref,
                debit_account=d, credit_account=c, amount=base_amt,
                total_debit=base_amt, total_credit=base_amt)
            d.post(debit_amount=base_amt)
            c.post(credit_amount=base_amt)

        if inv.invoice_type == "sales":
            diff = base_cash - base_relieved            # +ve => FX gain
            if diff >= 0:
                je(cash, ar, base_relieved)
                if diff > 0 and fx_gain:
                    je(cash, fx_gain, diff, "-fx")
            else:
                je(cash, ar, base_cash)
                if fx_loss:
                    je(fx_loss, ar, -diff, "-fx")
        else:
            diff = base_relieved - base_cash            # +ve => FX gain (paid less base)
            if diff >= 0:
                je(ap, cash, base_cash)
                if diff > 0 and fx_gain:
                    je(ap, fx_gain, diff, "-fx")
            else:
                je(ap, cash, base_relieved)
                if fx_loss:
                    je(fx_loss, cash, -diff, "-fx")

        self.posted = True
        self.save(update_fields=["posted"])
        inv.sync_paid_amount()
        msg = "تم تسجيل الدفعة وترحيلها"
        if base_cash != base_relieved:
            msg += f" — فرق صرف {abs(base_cash - base_relieved)}"
        return True, msg

    def company_or_default(self):
        from apps.core.models import Company
        return self.invoice.company or Company.objects.order_by("id").first()


class InvoiceItem(models.Model):
    """A single billed line on an Invoice — item, quantity, rate and the per-line
    VAT that ZATCA e-invoicing requires.

    Historic invoices entered as a flat subtotal (no line items) keep working:
    Invoice.recompute() owns the totals while there are no lines, and
    Invoice.recalculate_totals() takes over once at least one line exists.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    item = models.ForeignKey(
        "inventory.Item", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoice_lines",
    )
    item_code = models.CharField(max_length=100, blank=True)
    item_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    warehouse = models.ForeignKey(
        "core.Warehouse", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="invoice_lines",
    )
    qty = models.DecimalField(max_digits=18, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    tax_rate = models.DecimalField(max_digits=7, decimal_places=4, default=15)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)

    class Meta:
        db_table = "invoice_items"
        ordering = ["id"]

    def __str__(self):
        return f"{self.item_code or self.item_name} x{self.qty}"

    def save(self, *args, **kwargs):
        if self.item and not self.item_code:
            self.item_code = self.item.item_code
            self.item_name = self.item.item_name
        self.amount = (self.qty or Decimal(0)) * (self.rate or Decimal(0))
        self.tax_amount = (
            self.amount * (self.tax_rate or Decimal(0)) / Decimal(100)
        ).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)
