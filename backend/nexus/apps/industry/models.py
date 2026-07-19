from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models

from nexus.apps.core.models import Company, Branch, Warehouse
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import alphanumeric_validator, phone_validator

class IndustrySector(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    sku = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    description = models.TextField(blank=True)
    sector = models.ForeignKey(IndustrySector, on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)  # SAL-RULE-002 Stock Reservation
    min_reorder_level = models.PositiveIntegerField(default=10)
    reorder_quantity = models.PositiveIntegerField(default=50)
    last_reorder_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventories"
        unique_together = ['product', 'warehouse']

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name}"

    @property
    def needs_reorder(self):
        return self.quantity <= self.min_reorder_level

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def reserve(self, quantity):
        # SAL-RULE-002 Stock Reservation
        from django.core.exceptions import ValidationError
        if self.available_quantity < quantity:
            raise ValidationError('Insufficient available stock to reserve')
        self.reserved_quantity += quantity
        self.save(update_fields=['reserved_quantity'])

class Supplier(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True, validators=[phone_validator])
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True, blank=True)  # SAP-style document number (PO-YYYY-#####)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = generate_code(PurchaseOrder, 'po_number', 'PO')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number or self.id} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    @property
    def total(self):
        return self.quantity * self.unit_price
