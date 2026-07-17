from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from apps.core.models import Branch, Company, Warehouse
from apps.inventory.models import Item

PAYMENT_TERMS = [
    ("Net 15", "Net 15"),
    ("Net 30", "Net 30"),
    ("Net 60", "Net 60"),
    ("Due on Receipt", "Due on Receipt"),
    ("Advance", "Advance"),
]
PAYMENT_METHODS = [
    ("Bank Transfer", "Bank Transfer"),
    ("Cash", "Cash"),
    ("Cheque", "Cheque"),
    ("Credit Card", "Credit Card"),
]


class Supplier(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Blacklisted", "Blacklisted"),
    ]
    SUPPLIER_TYPES = [("Company", "Company"), ("Individual", "Individual")]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="suppliers"
    )
    name = models.CharField(max_length=255)
    supplier_type = models.CharField(
        max_length=50, choices=SUPPLIER_TYPES, default="Company"
    )
    contact_person = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="Saudi Arabia")
    bank_account = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS, blank=True)
    credit_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="SAR")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Active")
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)]
    )
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(
        null=True, blank=True,
        help_text="PRC-RULE-005: alerted for renewal 60 days before this date.",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    CONTRACT_RENEWAL_WINDOW_DAYS = 60

    def __str__(self):
        return self.name

    @property
    def days_to_contract_end(self):
        from datetime import date

        if not self.contract_end:
            return None
        return (self.contract_end - date.today()).days

    @property
    def contract_expires_soon(self):
        """PRC-RULE-005: within 60 days of contract expiry (or already past)."""
        d = self.days_to_contract_end
        return d is not None and d <= self.CONTRACT_RENEWAL_WINDOW_DAYS

    @property
    def contract_expired(self):
        d = self.days_to_contract_end
        return d is not None and d < 0


# PRC-CTRL-005: approval authority is tiered by PO value. Each tuple is
# (inclusive upper bound, role name); anything above the last bound needs the
# highest role. Ranks are the list order, so a higher role can always approve a
# lower tier.
APPROVAL_TIERS = [
    (Decimal("10000"), "Manager"),
    (Decimal("50000"), "Director"),
    (Decimal("100000"), "CFO"),
    (None, "CEO"),
]
APPROVAL_LADDER = [role for _, role in APPROVAL_TIERS]


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Received", "Received"),
        ("Cancelled", "Cancelled"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="purchase_orders"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="purchase_orders"
    )
    po_number = models.CharField(max_length=100, unique=True)
    transaction_date = models.DateField()
    required_by = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    total_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=10, default="SAR")
    payment_terms = models.CharField(max_length=50, choices=PAYMENT_TERMS, blank=True)
    discount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    incoterm = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("EXW", "EXW"),
            ("FOB", "FOB"),
            ("CIF", "CIF"),
            ("DDP", "DDP"),
            ("DAP", "DAP"),
        ],
    )
    approved_by = models.ForeignKey(
        "hr.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_purchase_orders",
    )
    cost_center = models.ForeignKey(
        "accounts.CostCenter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="purchase_orders",
    )
    project = models.ForeignKey(
        "pmo.Project", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="purchase_orders",
    )
    billed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Sum of invoice totals generated from this order. Maintained by "
        "Invoice.create_from_purchase_order().",
    )
    created_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_purchase_orders",
        help_text="Raiser of the PO. FIN-CTRL-002 forbids them approving it themselves.",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_tax(self):
        return sum((t.tax_amount for t in self.tax_charges.all()), 0)

    @property
    def total_paid(self):
        return sum((p.amount for p in self.payments.all()), 0)

    @property
    def outstanding_amount(self):
        return self.grand_total - self.total_paid

    @property
    def per_billed(self):
        """Percentage of this order's value already carried onto an invoice."""
        if not self.grand_total:
            return Decimal(0)
        return (Decimal(self.billed_amount) / Decimal(self.grand_total) * 100).quantize(Decimal("0.01"))

    def recalculate_totals(self):
        """Recompute totals from line items and tax charges. Called
        automatically via signals whenever items/taxes change."""
        items = list(self.items.all())
        self.total_qty = sum((i.qty for i in items), 0)
        self.total_amount = sum((i.amount for i in items), 0)
        subtotal_after_discount = self.total_amount - (self.discount or 0)
        self.grand_total = subtotal_after_discount + self.total_tax
        PurchaseOrder.objects.filter(pk=self.pk).update(
            total_qty=self.total_qty,
            total_amount=self.total_amount,
            grand_total=self.grand_total,
        )

    DELIVERY_ALERT_DAYS = 3

    @property
    def days_to_required_by(self):
        from datetime import date

        if not self.required_by:
            return None
        return (self.required_by - date.today()).days

    @property
    def delivery_due_soon(self):
        """PRC-RULE-002: required_by is within 3 days and the order is still
        open. A received or cancelled PO can't be late."""
        if self.status not in ("Submitted",):
            return False
        d = self.days_to_required_by
        return d is not None and d <= self.DELIVERY_ALERT_DAYS

    @property
    def delivery_overdue(self):
        if self.status not in ("Submitted",):
            return False
        d = self.days_to_required_by
        return d is not None and d < 0

    @property
    def required_approval_role(self):
        """PRC-CTRL-005: the lowest role authorised to approve this PO's value."""
        amount = Decimal(self.grand_total or 0)
        for bound, role in APPROVAL_TIERS:
            if bound is None or amount <= bound:
                return role
        return APPROVAL_LADDER[-1]

    def check_approval(self):
        """PRC-CTRL-005 (tiered authority) and FIN-CTRL-002 (segregation of
        duties) — both must hold before a PO leaves Draft."""
        from apps.rbac.models import RoleAssignment

        if self.approved_by is None:
            raise DjangoValidationError(
                f"PO of {self.grand_total} requires approval by "
                f"{self.required_approval_role}."
            )
        approver_user = self.approved_by.user
        if approver_user is None:
            raise DjangoValidationError(
                f"Approver {self.approved_by} has no linked user account, so their "
                f"approval authority can't be verified."
            )
        # FIN-CTRL-002: the creator can never sign off their own request, no
        # matter how senior they are.
        if self.created_by_id and approver_user.pk == self.created_by_id:
            raise DjangoValidationError(
                "Segregation of duties: the PO creator cannot approve their own order."
            )
        required_rank = APPROVAL_LADDER.index(self.required_approval_role)
        held = [
            a.role.name for a in
            RoleAssignment.objects.filter(user=approver_user).select_related("role")
        ]
        best = max(
            (APPROVAL_LADDER.index(r) for r in held if r in APPROVAL_LADDER),
            default=-1,
        )
        if best < required_rank:
            raise DjangoValidationError(
                f"PO of {self.grand_total} requires {self.required_approval_role} "
                f"approval; {self.approved_by} does not hold that authority."
            )

    def check_price_variance(self, threshold=Decimal("10")):
        """PRC-RULE-004: flag lines whose unit price moved more than `threshold`
        percent against the last submitted PO to this supplier for the same item.
        Returns a list of human-readable findings (advisory — the spec marks this
        as a flag, not a block)."""
        findings = []
        for line in self.items.select_related("item"):
            previous = (
                PurchaseOrderItem.objects
                .filter(purchase_order__supplier=self.supplier, item=line.item)
                .exclude(purchase_order=self)
                .exclude(purchase_order__status__in=["Draft", "Cancelled"])
                .order_by("-purchase_order__transaction_date", "-pk")
                .first()
            )
            if previous is None or not previous.rate:
                continue
            change = (Decimal(line.rate) - Decimal(previous.rate)) / Decimal(previous.rate) * 100
            if abs(change) > threshold:
                findings.append(
                    f"{line.item.item_code}: {previous.rate} -> {line.rate} "
                    f"({change.quantize(Decimal('0.01'))}%)"
                )
        return findings

    def three_way_match(self):
        """PRC-CTRL-001: PO vs Goods Receipts vs Invoices must agree.

        Returns (matched, discrepancies). Compares, per line, the ordered qty
        against the qty actually accepted on submitted GRNs, and the PO's value
        against what has been billed against it.
        """
        discrepancies = []
        for line in self.items.select_related("item"):
            accepted = line.accepted_qty
            if accepted != line.qty:
                discrepancies.append(
                    f"{line.item.item_code}: ordered {line.qty}, received {accepted}"
                )
        billed = Decimal(self.billed_amount or 0)
        if billed and billed != Decimal(self.grand_total or 0):
            discrepancies.append(
                f"invoiced {billed} against PO total {self.grand_total}"
            )
        return (not discrepancies), discrepancies

    def receive_stock(self):
        """Called when the PO transitions to 'Received'. Creates a Receipt
        StockEntry for every line item and marks them fully received."""
        from apps.inventory.models import StockEntry

        if not self.warehouse:
            raise DjangoValidationError(
                "Cannot mark a purchase order as Received without a warehouse set."
            )
        items = list(self.items.all())
        if not items:
            raise DjangoValidationError(
                "Cannot receive a purchase order with no line items."
            )
        with transaction.atomic():
            for line in items:
                StockEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    warehouse=self.warehouse,
                    item=line.item,
                    entry_type="Receipt",
                    quantity=line.qty,
                    rate=line.rate,
                    reference=f"PO {self.po_number}",
                )
                line.received_qty = line.qty
                PurchaseOrderItem.objects.filter(pk=line.pk).update(
                    received_qty=line.qty
                )

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    rate = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(0)]
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, editable=False, default=0
    )
    received_qty = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    @property
    def accepted_qty(self):
        """Quantity accepted across submitted goods receipts for this line.

        received_qty is a denormalised copy kept for the existing UI; this is the
        figure PRC-CTRL-001 matches against, derived from the GRNs themselves.
        """
        return sum(
            (r.qty_accepted for r in self.receipt_lines.filter(
                goods_receipt__status="Submitted"
            )),
            Decimal(0),
        )

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.rate
        super().save(*args, **kwargs)


class PurchaseTaxCharge(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="tax_charges"
    )
    description = models.CharField(max_length=255, default="VAT")
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=15, validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.description} ({self.tax_rate}%)"


class PurchasePayment(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="payments"
    )
    payment_date = models.DateField()
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHODS, default="Bank Transfer"
    )
    reference = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.amount}"


class GoodsReceipt(models.Model):
    """A physical delivery against a Purchase Order (GRN).

    Nothing recorded what actually arrived: PurchaseOrder.receive_stock() marked
    every line fully received in one shot, so a short or rejected delivery had
    nowhere to live and PRC-CTRL-001's three-way match had no middle document to
    match against.
    """

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Cancelled", "Cancelled"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="goods_receipts")
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="goods_receipts"
    )
    grn_number = models.CharField(max_length=100, unique=True)
    receipt_date = models.DateField()
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Where the goods landed. Defaults to the PO's warehouse.",
    )
    received_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="goods_receipts",
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-receipt_date", "-id"]

    def __str__(self):
        return self.grn_number

    def submit(self):
        """INV-CTRL-003: validate the whole receipt against the PO before any of
        it moves, then post accepted quantities into stock."""
        from apps.inventory.models import StockEntry

        if self.status != "Draft":
            raise DjangoValidationError("Only a draft goods receipt can be submitted.")
        if self.purchase_order.status not in ("Submitted", "Received"):
            raise DjangoValidationError(
                f"Cannot receive against a purchase order in status "
                f"'{self.purchase_order.status}'."
            )
        lines = list(self.items.select_related("po_item__item"))
        if not lines:
            raise DjangoValidationError("Cannot submit a goods receipt with no lines.")

        warehouse = self.warehouse or self.purchase_order.warehouse
        if warehouse is None:
            raise DjangoValidationError("Goods receipt has no warehouse to receive into.")

        # Validate every line first — a receipt is all-or-nothing.
        overages = []
        for line in lines:
            outstanding = line.po_item.qty - line.po_item.accepted_qty
            if line.qty_received > outstanding:
                overages.append(
                    f"{line.po_item.item.item_code}: receiving {line.qty_received} "
                    f"but only {outstanding} outstanding on the PO"
                )
        if overages:
            raise DjangoValidationError(
                f"Goods receipt exceeds the purchase order: {'; '.join(overages)}"
            )

        with transaction.atomic():
            for line in lines:
                if line.qty_accepted > 0:
                    StockEntry.objects.create(
                        company=self.company,
                        branch=self.purchase_order.branch,
                        warehouse=warehouse,
                        item=line.po_item.item,
                        entry_type="Receipt",
                        quantity=line.qty_accepted,
                        rate=line.po_item.rate,
                        reference=f"GRN {self.grn_number} (PO {self.purchase_order.po_number})",
                    )
            self.status = "Submitted"
            self.save(update_fields=["status"])
            # Roll the PO's received_qty up from its receipts.
            for po_line in self.purchase_order.items.all():
                PurchaseOrderItem.objects.filter(pk=po_line.pk).update(
                    received_qty=po_line.accepted_qty
                )
        return True, "تم استلام البضاعة / Goods received"


class GoodsReceiptItem(models.Model):
    goods_receipt = models.ForeignKey(
        GoodsReceipt, on_delete=models.CASCADE, related_name="items"
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem, on_delete=models.CASCADE, related_name="receipt_lines"
    )
    qty_received = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    qty_rejected = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    rejection_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["id"]

    @property
    def qty_accepted(self):
        return (self.qty_received or Decimal(0)) - (self.qty_rejected or Decimal(0))

    def clean(self):
        if (self.qty_rejected or Decimal(0)) > (self.qty_received or Decimal(0)):
            raise DjangoValidationError(
                {"qty_rejected": "Rejected quantity cannot exceed the quantity received."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class PurchaseRequisition(models.Model):
    """An internal request to buy something, ahead of any supplier commitment.

    PRC-RULE-001 requires an approved requisition to raise a PO automatically.
    There was no requisition at all: buying started at the PO, so the request
    and its approval lived outside the system.
    """

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Approved", "Approved"),
        ("Ordered", "Ordered"),
        ("Rejected", "Rejected"),
        ("Cancelled", "Cancelled"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="requisitions")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    pr_number = models.CharField(max_length=100, unique=True)
    transaction_date = models.DateField()
    required_by = models.DateField(null=True, blank=True)
    requested_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requisitions_raised",
    )
    approved_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requisitions_approved",
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-id"]

    def __str__(self):
        return self.pr_number

    def generate_purchase_orders(self):
        """PRC-RULE-001: raise a draft PO per preferred supplier.

        Item.supplier is the preferred supplier. Lines whose item has none are
        reported back rather than silently dropped — somebody has to source
        them by hand, and a silent skip is how a requisition quietly goes
        half-ordered.

        The generated POs are Drafts: PRC-CTRL-005 still requires an approver
        with the right authority before they can be submitted. Requisition
        approval buys the request, not the commitment.
        """
        if self.status != "Approved":
            raise DjangoValidationError(
                f"Only an approved requisition can raise purchase orders "
                f"(this one is '{self.status}')."
            )
        lines = list(self.items.select_related("item__supplier"))
        if not lines:
            raise DjangoValidationError("Requisition has no lines.")

        by_supplier, unsourced = {}, []
        for line in lines:
            supplier = line.item.supplier
            if supplier is None:
                unsourced.append(line.item.item_code)
                continue
            by_supplier.setdefault(supplier, []).append(line)

        created = []
        with transaction.atomic():
            for supplier, supplier_lines in by_supplier.items():
                po = PurchaseOrder.objects.create(
                    company=self.company, supplier=supplier, branch=self.branch,
                    warehouse=self.warehouse,
                    po_number=self._next_po_number(),
                    transaction_date=self.transaction_date,
                    required_by=self.required_by,
                    notes=f"تم الإنشاء من طلب الشراء {self.pr_number} / "
                          f"Generated from requisition {self.pr_number}",
                )
                for line in supplier_lines:
                    PurchaseOrderItem.objects.create(
                        purchase_order=po, item=line.item, qty=line.qty,
                        rate=line.rate or line.item.standard_rate or 0,
                    )
                    PurchaseRequisitionItem.objects.filter(pk=line.pk).update(
                        purchase_order=po
                    )
                created.append(po)
            if created and not unsourced:
                self.status = "Ordered"
                self.save(update_fields=["status"])
        return created, unsourced

    @staticmethod
    def _next_po_number():
        from datetime import date

        prefix = f"PO-PR-{date.today():%Y%m}-"
        seq = PurchaseOrder.objects.filter(po_number__startswith=prefix).count() + 1
        while PurchaseOrder.objects.filter(po_number=f"{prefix}{seq:04d}").exists():
            seq += 1
        return f"{prefix}{seq:04d}"


class PurchaseRequisitionItem(models.Model):
    requisition = models.ForeignKey(
        PurchaseRequisition, on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey("inventory.Item", on_delete=models.PROTECT, related_name="requisition_lines")
    qty = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    rate = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text="Estimated unit price. Falls back to the item's standard rate.",
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requisition_lines",
        help_text="Set once this line has been carried onto a PO.",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item.item_code} x{self.qty}"
