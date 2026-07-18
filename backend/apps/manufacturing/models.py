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
    approved_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_boms",
        help_text="MFG-CTRL-001: a BOM must be approved before production releases against it.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def raw_materials_cost(self):
        """Material cost for one full BOM batch (i.e. for `quantity` units)."""
        return sum((i.qty * i.rate for i in self.items.all()), 0)

    @property
    def is_approved(self):
        return self.approved_by_id is not None and self.approved_at is not None

    def approve(self, employee):
        from django.utils import timezone

        self.approved_by = employee
        self.approved_at = timezone.now()
        self.save(update_fields=["approved_by", "approved_at"])

    def requirements_for(self, output_qty):
        """MFG-RULE-001 (MRP): raw material needed to produce `output_qty` units.

        BOM.quantity is the batch size the recipe yields — a BOM that makes 10
        units from 5kg needs 50kg for 100 units, not 500. complete_production()
        multiplied the line qty by the output directly, silently assuming every
        BOM was a per-unit recipe.
        """
        from decimal import Decimal

        batch = Decimal(self.quantity or 1)
        if batch <= 0:
            batch = Decimal(1)
        factor = Decimal(output_qty) / batch
        return [
            (line, (Decimal(line.qty) * factor).quantize(Decimal("0.01")))
            for line in self.items.select_related("item")
        ]

    @property
    def cost_per_unit(self):
        """Batch cost spread over the units the batch yields."""
        from decimal import Decimal

        batch = Decimal(self.quantity or 1)
        if batch <= 0:
            return Decimal(0)
        return (Decimal(self.total_cost) / batch).quantize(Decimal("0.0001"))

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
    scrap_qty = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="MFG-RULE-005: units lost in production. Their cost is absorbed "
        "by the good units, raising the effective unit cost.",
    )
    uom = models.CharField(max_length=50, default="Unit")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    priority = models.CharField(
        max_length=50, choices=PRIORITY_CHOICES, default="Medium"
    )
    workstation_ref = models.ForeignKey(
        "Workstation", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="work_orders",
        help_text="MFG-CTRL-005: the machine this order runs on. Optional — the "
        "free-text `workstation` field predates this and still works.",
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

    def material_requirements(self):
        """MFG-RULE-001: explode the BOM for this work order's output quantity.

        Returns [(BOMItem, qty_required), ...].
        """
        if not self.bom:
            raise DjangoValidationError("Cannot run MRP without a BOM.")
        return self.bom.requirements_for(self.qty_to_produce)

    def check_material_availability(self):
        """MFG-CTRL-003: every raw material must be on hand *at this work
        order's warehouse* before the order releases or completes.

        This used to compare against item.stock_quantity — the company-wide
        total — so a work order could consume materials sitting in a warehouse
        it has no access to.
        """
        if not self.warehouse:
            raise DjangoValidationError(
                "Cannot check material availability without a warehouse."
            )
        shortages = []
        for line, required in self.material_requirements():
            available = line.item.stock_in_warehouse(self.warehouse)
            reserved = line.item.reserved_qty(self.warehouse, exclude_work_order=self)
            free = available - reserved
            if free < required:
                shortages.append(
                    f"{line.item.item_code} (free {free} at {self.warehouse.name}, "
                    f"need {required})"
                )
        if shortages:
            raise DjangoValidationError(
                f"Insufficient raw materials: {', '.join(shortages)}"
            )

    def release(self, ignore_bom_approval=False):
        """MFG-CTRL-001 + MFG-CTRL-003 + MFG-RULE-002: approve, check, reserve.

        Releasing is the point of no return for planning — it tells the shop
        floor the materials are theirs. So the BOM must be approved and the
        materials must exist before any reservation is written.
        """
        if not self.bom:
            raise DjangoValidationError("Cannot release a work order without a BOM.")
        if self.workstation_ref and self.workstation_ref.maintenance_overdue:
            # MFG-CTRL-005: preventive maintenance is enforced *before*
            # production, not reported after the machine has already run.
            due = self.workstation_ref.next_maintenance_due
            raise DjangoValidationError(
                f"Workstation {self.workstation_ref.code} is overdue for "
                f"maintenance{f' (due {due})' if due else ' (never serviced)'}; "
                f"it cannot be released to production."
            )
        if not ignore_bom_approval and not self.bom.is_approved:
            raise DjangoValidationError(
                f"BOM '{self.bom.bom_name}' is not approved; it cannot be released "
                f"to production."
            )
        self.check_material_availability()
        with transaction.atomic():
            self.reservations.all().delete()
            for line, required in self.material_requirements():
                MaterialReservation.objects.create(
                    work_order=self, item=line.item, warehouse=self.warehouse,
                    qty=required,
                )
            self.status = "In Progress"
            self.save(update_fields=["status"])
        return True, "تم إطلاق أمر الإنتاج وحجز المواد / Released and materials reserved"

    @property
    def yield_percent(self):
        """MFG-RULE-003: (actual / planned) * 100."""
        from decimal import Decimal

        if not self.qty_to_produce:
            return None
        return (
            Decimal(self.produced_qty) / Decimal(self.qty_to_produce) * 100
        ).quantize(Decimal("0.01"))

    @property
    def yield_variance_exceeded(self):
        """MFG-CTRL-004: alert when yield is more than 5% off plan."""
        from decimal import Decimal

        y = self.yield_percent
        return y is not None and abs(Decimal(100) - y) > Decimal(5)

    @property
    def effective_unit_cost(self):
        """MFG-RULE-005: scrap cost is absorbed by the units that survived, so
        the good output carries the true cost of the run."""
        from decimal import Decimal

        good = Decimal(self.produced_qty or 0)
        if good <= 0:
            return Decimal(0)
        return (Decimal(self.actual_cost or 0) / good).quantize(Decimal("0.0001"))

    def complete_production(self):
        """Called when the WorkOrder transitions to 'Completed'. Validates
        raw-material availability for the full BOM FIRST (all-or-nothing),
        then issues raw materials and receipts the finished good."""
        if self.produced_qty and self.produced_qty > 0:
            # Idempotency guard keyed on actual output, not on status: the
            # serializer sets status=Completed before calling this, so a
            # status check would block the first legitimate run too. produced_qty
            # is only written once production has actually happened.
            return
        if not self.bom:
            raise DjangoValidationError("Cannot complete a work order without a BOM.")
        if not self.warehouse:
            raise DjangoValidationError(
                "Cannot complete a work order without a warehouse."
            )
        requirements = self.material_requirements()
        if not requirements:
            raise DjangoValidationError("The linked BOM has no raw materials defined.")
        self.check_material_availability()

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
            # MFG-RULE-005: only the units that survived reach inventory, and
            # they carry the whole run's cost — scrap doesn't vanish, it makes
            # the good units more expensive.
            good_qty = Decimal(self.qty_to_produce) - Decimal(self.scrap_qty or 0)
            if good_qty < 0:
                raise DjangoValidationError(
                    f"Scrap ({self.scrap_qty}) cannot exceed the planned quantity "
                    f"({self.qty_to_produce})."
                )
            run_cost = Decimal(self.actual_cost or 0)
            if run_cost <= 0:
                run_cost = Decimal(self.bom.cost_per_unit) * Decimal(self.qty_to_produce)
            unit_rate = (run_cost / good_qty).quantize(Decimal("0.0001")) if good_qty else Decimal(0)
            if good_qty > 0:
                StockEntry.objects.create(
                    company=self.company,
                    branch=self.branch,
                    warehouse=self.warehouse,
                    item=self.item_to_manufacture,
                    entry_type="Receipt",
                    quantity=good_qty,
                    rate=unit_rate,
                    reference=f"WO {self.wo_number} production",
                )
            # The materials have physically moved, so the promise is spent.
            self.reservations.all().delete()
            WorkOrder.objects.filter(pk=self.pk).update(
                produced_qty=good_qty, status="Completed"
            )
            self.produced_qty = good_qty
            self.status = "Completed"

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


class MaterialReservation(models.Model):
    """MFG-RULE-002: raw material committed to a released work order.

    Without this, two work orders could both see the same stock as available and
    both release — the shortage only surfaced when the second one tried to
    complete, by which point the shop floor had already started.
    """

    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="reservations"
    )
    item = models.ForeignKey("inventory.Item", on_delete=models.CASCADE, related_name="reservations")
    warehouse = models.ForeignKey(
        "core.Warehouse", on_delete=models.CASCADE, related_name="material_reservations"
    )
    qty = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item.item_code} x{self.qty} for {self.work_order.wo_number}"


class Workstation(models.Model):
    """A machine or station on the shop floor.

    WorkOrder.workstation and JobCard.workstation are free-text strings, so
    there was nothing to hang a maintenance schedule on — no machine record
    existed at all. The text fields are left alone; this is additive.
    """

    company = models.ForeignKey(
        "core.CompanyProfile", on_delete=models.CASCADE, related_name="workstations"
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    branch = models.ForeignKey(
        "core.Branch", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workstations",
    )
    hour_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    maintenance_interval_days = models.PositiveIntegerField(
        default=0,
        help_text="MFG-CTRL-005: days between preventive services. 0 means no "
        "schedule, and is not enforced.",
    )
    last_maintenance_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="unique_workstation_code_per_company"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def next_maintenance_due(self):
        from datetime import timedelta

        if not self.maintenance_interval_days or not self.last_maintenance_date:
            return None
        return self.last_maintenance_date + timedelta(days=self.maintenance_interval_days)

    @property
    def days_to_maintenance(self):
        from datetime import date

        due = self.next_maintenance_due
        return None if due is None else (due - date.today()).days

    @property
    def maintenance_overdue(self):
        """MFG-CTRL-005: past its service date.

        A station with no interval configured is not on a schedule and is never
        overdue — otherwise this rule would halt every existing shop floor the
        day it shipped. A station with an interval but no recorded service has
        never been serviced, which counts as overdue.
        """
        if not self.maintenance_interval_days:
            return False
        if self.last_maintenance_date is None:
            return True
        return self.days_to_maintenance < 0

    def record_maintenance(self, on_date=None):
        from datetime import date

        self.last_maintenance_date = on_date or date.today()
        self.save(update_fields=["last_maintenance_date"])
        MaintenanceLog.objects.create(workstation=self, performed_on=self.last_maintenance_date)


class MaintenanceLog(models.Model):
    """The service history behind MFG-CTRL-005."""

    workstation = models.ForeignKey(
        Workstation, on_delete=models.CASCADE, related_name="maintenance_logs"
    )
    performed_on = models.DateField()
    performed_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="maintenance_performed",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_on", "-id"]

    def __str__(self):
        return f"{self.workstation.code} serviced {self.performed_on}"
