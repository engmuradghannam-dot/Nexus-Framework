from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.db import models, transaction

from apps.core.models import Branch, Company, Warehouse
from apps.core.validators import (
    ALLOWED_ATTACHMENT_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    validate_attachment_size,
    validate_image_size,
)


class ItemGroup(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="item_groups"
    )
    name = models.CharField(max_length=255)
    parent_group = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name


class Item(models.Model):
    ITEM_TYPES = [
        ("Stock", "Stock"),
        ("Service", "Service"),
        ("Asset", "Asset"),
        ("Bundle", "Bundle"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="items")
    item_code = models.CharField(max_length=100, unique=True)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES, default="Stock")
    item_group = models.ForeignKey(
        ItemGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)
    standard_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_stock_item = models.BooleanField(default=True)
    is_purchase_item = models.BooleanField(default=True)
    is_sales_item = models.BooleanField(default=True)
    is_service_item = models.BooleanField(default=False)
    reorder_level = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reorder_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default="Unit")
    barcode = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.CharField(
        max_length=100, blank=True, help_text="e.g. 30x20x10 cm"
    )
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    supplier = models.ForeignKey(
        "buying.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    tax_category = models.CharField(max_length=100, blank=True)
    valuation_method = models.CharField(
        max_length=50,
        default="FIFO",
        choices=[
            ("FIFO", "FIFO"),
            ("LIFO", "LIFO"),
            ("Moving Average", "Moving Average"),
        ],
    )
    image = models.ImageField(
        upload_to="item_images/",
        blank=True,
        null=True,
        validators=[
            validate_image_size,
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
        ],
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name

    @property
    def stock_quantity(self):
        total = 0
        for entry in self.stockentry_set.all():
            if entry.entry_type == "Receipt":
                total += entry.quantity
            elif entry.entry_type == "Issue":
                total -= entry.quantity
        return total

    def fefo_batches(self, warehouse, qty):
        """WHS-RULE-005: allocate `qty` across batches, nearest expiry first.

        Returns [(ItemBatch, qty_from_that_batch), ...]. Batches with no expiry
        date are used last — an undated batch shouldn't jump ahead of one that
        is about to expire. Raises if the warehouse can't cover the quantity.
        """
        from django.core.exceptions import ValidationError
        from django.db.models import F

        batches = list(
            self.batches.filter(warehouse=warehouse, quantity__gt=0)
            .order_by(F("expiry_date").asc(nulls_last=True), "id")
        )
        remaining = Decimal(qty)
        plan = []
        for batch in batches:
            if remaining <= 0:
                break
            take = min(Decimal(batch.quantity), remaining)
            plan.append((batch, take))
            remaining -= take
        if remaining > 0:
            available = sum((Decimal(b.quantity) for b in batches), Decimal(0))
            raise ValidationError(
                f"Insufficient batch stock for {self.item_code} at {warehouse.name}: "
                f"need {qty}, batched {available}."
            )
        return plan

    def valuation_rate(self, warehouse=None):
        """INV-RULE-003: unit cost used for COGS, per this item's valuation_method.

        The spec sheet is self-contradictory here — 'Modules Overview' says
        FIFO/FEFO while INV-RULE-003 says weighted average — so this defers to
        Item.valuation_method, which already exists per item and lets both hold.
        Returns Decimal(0) when there is nothing on hand to value.
        """
        entries = self.stockentry_set.filter(entry_type="Receipt")
        if warehouse is not None:
            entries = entries.filter(warehouse=warehouse)
        entries = list(entries.order_by("posting_date", "id"))
        if not entries:
            return Decimal(0)

        method = self.valuation_method
        if method == "FIFO":
            return Decimal(entries[0].rate)
        if method == "LIFO":
            return Decimal(entries[-1].rate)
        # Moving Average (and anything unrecognised): total cost / total qty.
        qty = sum((Decimal(e.quantity) for e in entries), Decimal(0))
        if qty <= 0:
            return Decimal(0)
        cost = sum((Decimal(e.quantity) * Decimal(e.rate) for e in entries), Decimal(0))
        return (cost / qty).quantize(Decimal("0.0001"))

    def cogs_for(self, qty, warehouse=None):
        """INV-RULE-003: cost of goods sold for `qty` units."""
        return (Decimal(qty) * self.valuation_rate(warehouse)).quantize(Decimal("0.01"))

    def reserved_qty(self, warehouse, exclude_work_order=None, exclude_sales_order=None):
        """Units at a warehouse already promised to someone.

        Covers BOTH production (MFG-RULE-002) and sales (SAL-RULE-002). They
        must be counted together: stock promised to a work order is not
        available to promise to a customer, and vice versa. Netting only one of
        them would let the two sides commit the same units twice — which is the
        exact failure reservations exist to prevent.
        """
        from django.db.models import Sum

        mfg = self.reservations.filter(
            warehouse=warehouse, work_order__status="In Progress"
        )
        if exclude_work_order is not None and exclude_work_order.pk:
            mfg = mfg.exclude(work_order=exclude_work_order)
        mfg_total = mfg.aggregate(q=Sum("qty"))["q"] or Decimal(0)

        sales = self.sales_reservations.filter(
            warehouse=warehouse, sales_order__status="Submitted"
        )
        if exclude_sales_order is not None and exclude_sales_order.pk:
            sales = sales.exclude(sales_order=exclude_sales_order)
        sales_total = sales.aggregate(q=Sum("qty"))["q"] or Decimal(0)

        return mfg_total + sales_total

    def available_qty(self, warehouse, **exclusions):
        """On hand minus everything already promised."""
        return self.stock_in_warehouse(warehouse) - self.reserved_qty(warehouse, **exclusions)

    def stock_in_warehouse(self, warehouse):
        """On-hand quantity of this item at one warehouse.

        ``stock_quantity`` sums every StockEntry regardless of location, so it
        answers "how much of this item does the company own", not "how much can
        I ship from here". Callers that issue stock out of a specific warehouse
        (sales delivery, production consumption) need this one — otherwise an
        order ships from an empty warehouse whenever some *other* warehouse
        happens to hold the item.
        """
        from django.db.models import Case, DecimalField, Sum, When

        if warehouse is None:
            return Decimal(0)
        agg = self.stockentry_set.filter(warehouse=warehouse).aggregate(
            qty=Sum(
                Case(
                    When(entry_type="Receipt", then="quantity"),
                    When(entry_type="Issue", then=-models.F("quantity")),
                    default=Decimal(0),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                )
            )
        )
        return agg["qty"] or Decimal(0)


class ItemSerialNumber(models.Model):
    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Sold", "Sold"),
        ("Reserved", "Reserved"),
        ("Scrapped", "Scrapped"),
    ]
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="serial_numbers"
    )
    serial_no = models.CharField(max_length=100, unique=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="Available"
    )
    warranty_expiry = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.serial_no


class ItemBatch(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="batches")
    batch_no = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    expiry_date = models.DateField(null=True, blank=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ("item", "batch_no")

    def __str__(self):
        return f"{self.item.item_code} - {self.batch_no}"

    @property
    def days_to_expiry(self):
        from datetime import date

        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    @property
    def is_expiring_soon(self):
        """INV-RULE-005: within 30 days of expiry (or already past it)."""
        d = self.days_to_expiry
        return d is not None and d <= 30

    @property
    def is_expired(self):
        d = self.days_to_expiry
        return d is not None and d < 0


class StockEntry(models.Model):
    ENTRY_TYPES = [("Receipt", "Receipt"), ("Issue", "Issue"), ("Transfer", "Transfer")]
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Cancelled", "Cancelled"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    bin_location = models.ForeignKey(
        "core.BinLocation", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="stock_entries",
        help_text="WHS-CTRL-001: required once the warehouse has bins defined.",
    )
    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    target_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    uom = models.CharField(max_length=50, default="Unit")
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    posting_date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="Submitted"
    )
    created_by = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    @property
    def total_cost(self):
        return self.quantity * self.rate

    def __str__(self):
        return f"{self.entry_type} - {self.item.item_code}"


class StockReconciliation(models.Model):
    REASON_CHOICES = [
        ("Physical Count", "Physical Count"),
        ("Damage", "Damage"),
        ("Theft", "Theft"),
        ("System Error", "System Error"),
        ("Other", "Other"),
    ]
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Cancelled", "Cancelled"),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="stock_reconciliations"
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    reconciliation_date = models.DateField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    reason = models.CharField(
        max_length=50, choices=REASON_CHOICES, default="Physical Count"
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    approved_by = models.ForeignKey(
        "hr.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_reconciliations",
    )
    attachment = models.FileField(
        upload_to="stock_reconciliation_attachments/",
        blank=True,
        null=True,
        validators=[
            validate_attachment_size,
            FileExtensionValidator(ALLOWED_ATTACHMENT_EXTENSIONS),
        ],
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_difference_value(self):
        return sum((i.total_difference_value for i in self.items.all()), 0)

    def apply_adjustments(self):
        """Called when the reconciliation transitions to 'Submitted'.
        Creates a Receipt/Issue StockEntry per line to bring actual system
        stock in line with the counted quantity."""
        lines = list(self.items.all())
        if not lines:
            raise DjangoValidationError(
                "Cannot submit a stock reconciliation with no counted items."
            )
        with transaction.atomic():
            for line in lines:
                diff = line.difference
                if diff == 0:
                    continue
                StockEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    warehouse=self.warehouse,
                    item=line.item,
                    entry_type="Receipt" if diff > 0 else "Issue",
                    quantity=abs(diff),
                    rate=line.unit_cost,
                    reference=f"Stock Reconciliation SR-{self.id}",
                )

    def __str__(self):
        return f"SR-{self.id} - {self.warehouse}"


class StockReconciliationItem(models.Model):
    reconciliation = models.ForeignKey(
        StockReconciliation, on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    system_quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    @property
    def difference(self):
        return self.actual_quantity - self.system_quantity

    @property
    def total_difference_value(self):
        return self.difference * self.unit_cost

    def __str__(self):
        return f"{self.item.item_code} ({self.difference})"
