from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

from apps.core.models import Branch, Company, Warehouse
from apps.inventory.models import Item, StockEntry


class BOM(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="boms")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="boms")
    bom_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, default="1.0")
    quantity = models.DecimalField(max_digits=18, decimal_places=2, default=1)
    uom = models.CharField(max_length=50, default="Unit")
    operating_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def raw_materials_cost(self):
        return sum((i.qty * i.rate for i in self.items.all()), 0)

    @property
    def total_cost(self):
        return self.raw_materials_cost + self.operating_cost + self.labor_cost

    def __str__(self):
        return self.bom_name


class BOMItem(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.DecimalField(
        max_digits=18, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    uom = models.CharField(max_length=50, default="Unit")
    rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)


class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]
    PRIORITY_CHOICES = [
        ("Low", "Low"),
        ("Medium", "Medium"),
        ("High", "High"),
        ("Urgent", "Urgent"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="work_orders"
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True)
    wo_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateField(auto_now_add=True)
    item_to_manufacture = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty_to_produce = models.DecimalField(max_digits=18, decimal_places=2)
    produced_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    uom = models.CharField(max_length=50, default="Unit")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    priority = models.CharField(
        max_length=50, choices=PRIORITY_CHOICES, default="Medium"
    )
    workstation = models.CharField(max_length=255, blank=True)
    supervisor = models.ForeignKey(
        "hr.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_work_orders",
    )
    planned_start = models.DateField(null=True, blank=True)
    planned_end = models.DateField(null=True, blank=True)
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def complete_production(self):
        """Called when the WorkOrder transitions to 'Completed'. Validates
        raw-material availability for the full BOM FIRST (all-or-nothing),
        then issues raw materials and receipts the finished good."""
        if not self.bom:
            raise DjangoValidationError("Cannot complete a work order without a BOM.")
        if not self.warehouse:
            raise DjangoValidationError(
                "Cannot complete a work order without a warehouse."
            )
        bom_items = list(self.bom.items.all())
        if not bom_items:
            raise DjangoValidationError("The linked BOM has no raw materials defined.")

        shortages = []
        requirements = []
        for bom_item in bom_items:
            required = bom_item.qty * self.qty_to_produce
            available = bom_item.item.stock_quantity
            requirements.append((bom_item, required))
            if available < required:
                shortages.append(
                    f"{bom_item.item.item_code} (available {available}, need {required})"
                )
        if shortages:
            raise DjangoValidationError(
                f"Insufficient raw materials to complete production: {', '.join(shortages)}"
            )

        with transaction.atomic():
            for bom_item, required in requirements:
                StockEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    warehouse=self.warehouse,
                    item=bom_item.item,
                    entry_type="Issue",
                    quantity=required,
                    rate=bom_item.rate,
                    reference=f"WO {self.wo_number} consumption",
                )
            StockEntry.objects.create(
                company=self.company,
                branch=self.branch,
                warehouse=self.warehouse,
                item=self.item_to_manufacture,
                entry_type="Receipt",
                quantity=self.qty_to_produce,
                rate=(
                    (self.actual_cost / self.qty_to_produce)
                    if self.qty_to_produce
                    else 0
                ),
                reference=f"WO {self.wo_number} production",
            )
            WorkOrder.objects.filter(pk=self.pk).update(
                produced_qty=self.qty_to_produce
            )

    def __str__(self):
        return self.wo_number


class JobCard(models.Model):
    """بطاقة العمل - shop-floor tracking of a single operation against a
    Work Order: who ran it, on which workstation, for how long, and how
    much of the planned quantity actually got completed."""

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Work In Progress", "Work In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="job_cards")
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="job_cards")
    operation = models.CharField(max_length=255)
    workstation = models.CharField(max_length=255, blank=True)
    employee = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="job_cards",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")
    for_quantity = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    completed_qty = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    started_time = models.DateTimeField(null=True, blank=True)
    ended_time = models.DateTimeField(null=True, blank=True)
    hour_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_operating_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0, editable=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.operation}"

    @property
    def time_in_mins(self):
        if self.started_time and self.ended_time:
            return round((self.ended_time - self.started_time).total_seconds() / 60, 2)
        return 0

    def start(self):
        from django.utils import timezone

        if self.status != "Open":
            return False, "لا يمكن البدء إلا لبطاقة عمل مفتوحة"
        self.status = "Work In Progress"
        self.started_time = timezone.now()
        self.save(update_fields=["status", "started_time"])
        return True, "تم بدء العملية"

    def complete(self, completed_qty=None):
        from django.utils import timezone

        if self.status != "Work In Progress":
            return False, "لا يمكن الإكمال إلا لبطاقة عمل قيد التنفيذ"
        qty = Decimal(str(completed_qty)) if completed_qty is not None else self.for_quantity
        if qty <= 0:
            return False, "الكمية المكتملة يجب أن تكون أكبر من صفر"
        if self.for_quantity and qty > self.for_quantity:
            return False, f"الكمية المكتملة ({qty}) تتجاوز الكمية المخططة ({self.for_quantity})"
        self.ended_time = timezone.now()
        self.completed_qty = qty
        self.actual_operating_cost = (Decimal(str(self.time_in_mins)) / Decimal(60)) * (self.hour_rate or 0)
        self.status = "Completed"
        self.save(update_fields=["status", "ended_time", "completed_qty", "actual_operating_cost"])
        return True, "تم إكمال العملية"


class QualityInspection(models.Model):
    """فحص الجودة - a quality check against an item, optionally tied back to
    the Purchase Order (incoming inspection) or Work Order (in-process/final
    inspection) that triggered it."""

    INSPECTION_TYPES = [
        ("Incoming", "Incoming"),
        ("In Process", "In Process"),
        ("Final", "Final"),
        ("Outgoing", "Outgoing"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Rejected", "Rejected"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="quality_inspections")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="quality_inspections")
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPES, default="Incoming")
    reference_purchase_order = models.ForeignKey(
        "buying.PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="quality_inspections",
    )
    reference_work_order = models.ForeignKey(
        WorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="quality_inspections",
    )
    sample_size = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    inspected_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True, related_name="quality_inspections",
    )
    inspection_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inspection_date", "-id"]

    def __str__(self):
        return f"{self.item.item_code} - {self.get_inspection_type_display()} ({self.status})"

    def recalculate_status(self):
        """Derive Accepted/Rejected from parameter readings once any exist;
        a single failed parameter fails the whole inspection. No-op (stays
        Pending) until at least one parameter has been recorded."""
        params = list(self.parameters.all())
        if not params:
            return
        overall = "Rejected" if any(p.status == "Rejected" for p in params) else "Accepted"
        QualityInspection.objects.filter(pk=self.pk).update(status=overall)
        self.status = overall


class QualityInspectionParameter(models.Model):
    STATUS_CHOICES = [("Accepted", "Accepted"), ("Rejected", "Rejected")]

    inspection = models.ForeignKey(QualityInspection, on_delete=models.CASCADE, related_name="parameters")
    parameter = models.CharField(max_length=255)
    specification = models.CharField(max_length=255, blank=True)
    min_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    max_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    reading_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Accepted")

    def save(self, *args, **kwargs):
        if self.reading_value is not None and (self.min_value is not None or self.max_value is not None):
            below = self.min_value is not None and self.reading_value < self.min_value
            above = self.max_value is not None and self.reading_value > self.max_value
            self.status = "Rejected" if (below or above) else "Accepted"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parameter}: {self.reading_value} ({self.status})"
