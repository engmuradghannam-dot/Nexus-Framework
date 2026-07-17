from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from apps.buying.models import PAYMENT_METHODS, PAYMENT_TERMS
from apps.core.models import Branch, Company, Warehouse
from apps.inventory.models import Item


class Customer(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Blacklisted", "Blacklisted"),
    ]
    CUSTOMER_TYPES = [("Company", "Company"), ("Individual", "Individual")]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    customer_type = models.CharField(
        max_length=50, choices=CUSTOMER_TYPES, default="Company"
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
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="sales_orders"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="sales_orders"
    )
    so_number = models.CharField(max_length=100, unique=True)
    transaction_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
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
    sales_person = models.ForeignKey(
        "hr.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales_orders_handled",
    )
    cost_center = models.ForeignKey(
        "accounts.CostCenter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sales_orders",
    )
    project = models.ForeignKey(
        "pmo.Project", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sales_orders",
    )
    billed_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Sum of invoice totals generated from this order. Maintained by "
        "Invoice.create_from_sales_order().",
    )
    backorder_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="backorders",
        help_text="SAL-RULE-004: set when this order carries quantities that the "
        "original order could not fulfil.",
    )
    discount_approved_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_sales_discounts",
        help_text="Manager who authorised a discount above 10% (SAL-CTRL-004).",
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
        items = list(self.items.all())
        self.total_qty = sum((i.qty for i in items), 0)
        self.total_amount = sum((i.amount for i in items), 0)
        subtotal_after_discount = self.total_amount - (self.discount or 0)
        self.grand_total = subtotal_after_discount + self.total_tax
        SalesOrder.objects.filter(pk=self.pk).update(
            total_qty=self.total_qty,
            total_amount=self.total_amount,
            grand_total=self.grand_total,
        )

    @property
    def discount_percent(self):
        """Document discount as a percentage of the pre-discount line total."""
        if not self.total_amount:
            return Decimal(0)
        return (Decimal(self.discount or 0) / Decimal(self.total_amount) * 100).quantize(
            Decimal("0.01")
        )

    def check_credit_limit(self):
        """CRM-CTRL-001 / SAL-CTRL-001: block confirmation when the customer's
        outstanding balance plus this order would breach their credit limit.

        credit_limit already existed on Customer but nothing read it. A zero
        limit means "not configured" and is not enforced, so existing customers
        keep working until a limit is actually set.
        """
        limit = Decimal(self.customer.credit_limit or 0)
        if limit <= 0:
            return
        other_outstanding = sum(
            (Decimal(so.outstanding_amount) for so in
             SalesOrder.objects.filter(customer=self.customer)
             .exclude(pk=self.pk)
             .exclude(status__in=["Draft", "Cancelled"])),
            Decimal(0),
        )
        exposure = other_outstanding + Decimal(self.outstanding_amount)
        if exposure > limit:
            raise DjangoValidationError(
                f"Credit limit exceeded for {self.customer.name}: "
                f"exposure {exposure} > limit {limit}."
            )

    def check_discount_authorization(self):
        """SAL-CTRL-004 / CRM-RULE-005: a discount over 10% needs manager sign-off."""
        if self.discount_percent > Decimal(10) and not self.discount_approved_by_id:
            raise DjangoValidationError(
                f"Discount of {self.discount_percent}% exceeds 10% and requires "
                f"manager approval."
            )

    def reserve_stock(self):
        """SAL-RULE-002 + SAL-RULE-004: commit what's available, backorder the rest.

        Called on Draft -> Submitted. Unlike deliver_stock() this does not
        refuse when stock is short: the spec's answer to a shortage is a
        backorder, not a rejection — the customer's order is real either way,
        and refusing it loses the demand signal.

        Returns (reservations_created, backorder or None).
        """
        if not self.warehouse:
            raise DjangoValidationError("Cannot reserve stock without a warehouse.")
        lines = list(self.items.select_related("item"))
        if not lines:
            raise DjangoValidationError("Cannot confirm an order with no line items.")

        shortfalls = []
        with transaction.atomic():
            self.reservations.all().delete()
            reserved = 0
            for line in lines:
                available = line.item.available_qty(
                    self.warehouse, exclude_sales_order=self
                )
                take = min(max(available, Decimal(0)), Decimal(line.qty))
                short = Decimal(line.qty) - take
                if take > 0:
                    StockReservation.objects.create(
                        sales_order=self, item=line.item,
                        warehouse=self.warehouse, qty=take,
                    )
                    reserved += 1
                if short > 0:
                    shortfalls.append((line, short))
                    SalesOrderItem.objects.filter(pk=line.pk).update(backordered_qty=short)

            backorder = self._create_backorder(shortfalls) if shortfalls else None
        return reserved, backorder

    def _create_backorder(self, shortfalls):
        """SAL-RULE-004: a Draft order holding only the unfulfillable quantities.

        It stays Draft rather than confirming itself — confirming would try to
        reserve stock that by definition isn't there, and would loop.
        """
        backorder = SalesOrder.objects.create(
            company=self.company, customer=self.customer,
            so_number=self._next_backorder_number(),
            transaction_date=self.transaction_date,
            delivery_date=self.delivery_date,
            branch=self.branch, warehouse=self.warehouse,
            currency=self.currency, status="Draft",
            backorder_of=self,
            notes=f"طلب مؤجل من {self.so_number} / Backorder from {self.so_number}",
        )
        for line, short in shortfalls:
            SalesOrderItem.objects.create(
                sales_order=backorder, item=line.item, qty=short, rate=line.rate,
            )
        backorder.recalculate_totals()
        return backorder

    def _next_backorder_number(self):
        base = f"{self.so_number}-BO"
        n = 1
        while SalesOrder.objects.filter(so_number=f"{base}{n}").exists():
            n += 1
        return f"{base}{n}"

    def deliver_stock(self):
        """Called when the SO transitions to 'Delivered'. Validates enough
        stock exists for every line BEFORE issuing anything (all-or-nothing),
        then creates an Issue StockEntry per line."""
        from apps.inventory.models import StockEntry

        if not self.warehouse:
            raise DjangoValidationError(
                "Cannot mark a sales order as Delivered without a warehouse set."
            )
        items = list(self.items.all())
        if not items:
            raise DjangoValidationError(
                "Cannot deliver a sales order with no line items."
            )
        shortages = []
        for line in items:
            # Per SAL-CTRL-002 the check must be against the warehouse we are
            # shipping from. item.stock_quantity is the company-wide total, so
            # using it let an order ship out of an empty warehouse whenever any
            # other warehouse held the item.
            available = line.item.stock_in_warehouse(self.warehouse)
            if available < line.qty:
                shortages.append(
                    f"{line.item.item_code} (available {available} at {self.warehouse.name}, "
                    f"need {line.qty})"
                )
        if shortages:
            raise DjangoValidationError(
                f"Insufficient stock to deliver: {', '.join(shortages)}"
            )
        with transaction.atomic():
            for line in items:
                StockEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    warehouse=self.warehouse,
                    item=line.item,
                    entry_type="Issue",
                    quantity=line.qty,
                    rate=line.rate,
                    reference=f"SO {self.so_number}",
                )
                SalesOrderItem.objects.filter(pk=line.pk).update(delivered_qty=line.qty)
            # The goods have physically left, so the promise is spent.
            self.reservations.all().delete()

    def __str__(self):
        return self.so_number


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="items"
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
    delivered_qty = models.DecimalField(
        max_digits=18, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    backordered_qty = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="SAL-RULE-004: quantity moved onto a backorder because stock "
        "was short at confirmation.",
    )

    def save(self, *args, **kwargs):
        self.amount = self.qty * self.rate
        super().save(*args, **kwargs)


class SalesTaxCharge(models.Model):
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="tax_charges"
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


class SalesPayment(models.Model):
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="payments"
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
        return f"{self.sales_order.so_number} - {self.amount}"


class StockReservation(models.Model):
    """SAL-RULE-002: stock committed to a confirmed sales order.

    Item.reserved_qty() nets these against production reservations, so a
    confirmed customer order and a released work order can't both claim the
    same units.
    """

    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="reservations"
    )
    item = models.ForeignKey(
        "inventory.Item", on_delete=models.CASCADE, related_name="sales_reservations"
    )
    warehouse = models.ForeignKey(
        "core.Warehouse", on_delete=models.CASCADE, related_name="sales_reservations"
    )
    qty = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item.item_code} x{self.qty} for {self.sales_order.so_number}"
