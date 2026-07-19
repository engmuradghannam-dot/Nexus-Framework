from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from nexus.apps.core.models import Company, Branch, Warehouse
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import alphanumeric_validator
from nexus.apps.industry.models import Product


class WorkCenter(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_centers')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_centers')
    description = models.TextField(blank=True)
    capacity_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operating_cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"


class BOM(models.Model):
    """Bill of Materials"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boms')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boms', null=True, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        unique_together = ['product', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"BOM {self.product.name} v{self.version}"

    @property
    def total_cost(self):
        return sum(item.total_cost for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()


class BOMItem(models.Model):
    """Individual item in a BOM"""
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_usages')
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['bom', 'component']

    def __str__(self):
        return f"{self.bom.product.name} -> {self.component.name} ({self.quantity})"

    @property
    def total_cost(self):
        effective_qty = self.quantity * (1 + self.scrap_percentage / 100)
        return effective_qty * self.unit_cost

    @property
    def effective_quantity(self):
        return self.quantity * (1 + self.scrap_percentage / 100)


class Routing(models.Model):
    """Production routing / operations sequence"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='routings')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='routings', null=True, blank=True)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    total_estimated_time = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"Routing {self.product.name} v{self.version}"

    @property
    def operation_count(self):
        return self.operations.count()

    @property
    def total_cost(self):
        return sum(op.total_cost for op in self.operations.all())


class RoutingOperation(models.Model):
    """Individual operation in a routing"""
    routing = models.ForeignKey(Routing, on_delete=models.CASCADE, related_name='operations')
    sequence = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations')
    setup_time = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    run_time_per_unit = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    labor_cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overhead_cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_mandatory = models.BooleanField(default=True)
    quality_check_required = models.BooleanField(default=False)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"Op {self.sequence}: {self.name}"

    @property
    def total_cost(self):
        if self.work_center:
            return self.setup_time * self.work_center.operating_cost_per_hour
        return 0


class ManufacturingOrder(models.Model):
    """Production order / work order"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('released', 'Released'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    order_number = models.CharField(max_length=50, unique=True, blank=True)  # MO-YYYY-#####
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='manufacturing_orders')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='manufacturing_orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='manufacturing_orders')
    bom = models.ForeignKey(BOM, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    routing = models.ForeignKey(Routing, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    quantity = models.PositiveIntegerField(default=1)
    quantity_produced = models.PositiveIntegerField(default=0)
    quantity_rejected = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    planned_start = models.DateTimeField(null=True, blank=True)
    planned_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_manufacturing_orders')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_manufacturing_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_code(ManufacturingOrder, 'order_number', 'MO')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MO-{self.order_number} ({self.product.name})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.planned_start and self.planned_end and self.planned_end < self.planned_start:
            raise ValidationError('Planned end must be on or after planned start')

    @property
    def completion_percentage(self):
        if self.quantity == 0:
            return 0
        return round(self.quantity_produced / self.quantity * 100, 2)

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.planned_end and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.planned_end
        return False

    @property
    def remaining_quantity(self):
        return max(0, self.quantity - self.quantity_produced)

    @property
    def yield_percentage(self):
        total = self.quantity_produced + self.quantity_rejected
        if total == 0:
            return 0
        return round(self.quantity_produced / total * 100, 2)


class ManufacturingOrderOperation(models.Model):
    """Operation execution tracking for a manufacturing order"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]

    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='operations')
    routing_operation = models.ForeignKey(RoutingOperation, on_delete=models.SET_NULL, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    work_center = models.ForeignKey(WorkCenter, on_delete=models.SET_NULL, null=True, blank=True)
    setup_start = models.DateTimeField(null=True, blank=True)
    setup_end = models.DateTimeField(null=True, blank=True)
    run_start = models.DateTimeField(null=True, blank=True)
    run_end = models.DateTimeField(null=True, blank=True)
    quantity_produced = models.PositiveIntegerField(default=0)
    quantity_rejected = models.PositiveIntegerField(default=0)
    actual_setup_time = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    actual_run_time = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"MO-{self.manufacturing_order.order_number} Op{self.sequence}"

    @property
    def total_time(self):
        return self.actual_setup_time + self.actual_run_time


class MaterialRequisition(models.Model):
    """Material request for manufacturing"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('issued', 'Issued'),
        ('partial', 'Partially Issued'),
        ('rejected', 'Rejected'),
    ]

    requisition_number = models.CharField(max_length=50, unique=True, blank=True)  # MR-YYYY-#####
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='requisitions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='material_requisitions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_requisitions')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requisitions')
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            self.requisition_number = generate_code(MaterialRequisition, 'requisition_number', 'MR')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"MR-{self.requisition_number}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_cost(self):
        return sum(item.total_cost for item in self.items.all())


class MaterialRequisitionItem(models.Model):
    """Individual item in a material requisition"""
    requisition = models.ForeignKey(MaterialRequisition, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    quantity_issued = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['requisition', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity_requested}"

    @property
    def total_cost(self):
        return self.quantity_issued * self.unit_cost

    @property
    def fulfillment_percentage(self):
        if self.quantity_requested == 0:
            return 0
        return round(self.quantity_issued / self.quantity_requested * 100, 2)
