from decimal import Decimal

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from nexus.apps.core.models import Warehouse
from nexus.apps.core.utils import generate_code
from nexus.apps.crm.models import Customer
from nexus.apps.industry.models import Inventory, Product


def today():
    # A module-level function (not a lambda) so Django's migration writer
    # can serialize this default - lambdas aren't importable/referenceable.
    return timezone.now().date()


class SalesOrder(models.Model):
    """SAL module - sales_orders table."""

    STATUS_CHOICES = [
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('picking', 'Picking'),
        ('packed', 'Packed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'),
        ('invoiced', 'Invoiced'), ('paid', 'Paid'), ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'), ('credit_card', 'Credit Card'), ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'), ('credit', 'Credit'),
    ]

    VAT_RATE = Decimal('0.15')

    so_id = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField(default=today)
    required_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_rep = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='sales_orders')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='credit')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    shipping_address = models.TextField(max_length=500, validators=[MinLengthValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.so_id:
            self.so_id = generate_code(SalesOrder, 'so_id', 'SO')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.so_id

    def clean(self):
        from django.core.exceptions import ValidationError
        # SAL-Inputs validation: discount <= 30% of total
        if self.discount_amount and self.total_amount and self.discount_amount > self.total_amount * Decimal('0.30'):
            raise ValidationError('Discount cannot exceed 30% of total amount')
        # SAL-Inputs: order_date not future, required_date >= order_date
        if self.order_date and self.order_date > timezone.now().date():
            raise ValidationError('Order date cannot be in the future')
        if self.required_date and self.order_date and self.required_date < self.order_date:
            raise ValidationError('Required date must be on or after the order date')

    @property
    def discount_pct(self):
        if not self.total_amount:
            return Decimal('0.00')
        return (Decimal(self.discount_amount) / Decimal(self.total_amount) * 100).quantize(Decimal('0.01'))

    @property
    def requires_discount_approval(self):
        # SAL-CTRL-004 Discount Authorization
        return self.discount_pct > 10

    def check_credit(self):
        # SAL-CTRL-001 Credit Check
        return not self.customer.exceeds_credit_limit(self.total_amount)

    def calculate_tax(self):
        # SAL-Inputs: tax_amount auto-calculated at 15% VAT
        taxable = self.total_amount - self.discount_amount
        self.tax_amount = (taxable * self.VAT_RATE).quantize(Decimal('0.01'))
        return self.tax_amount

    def reserve_stock(self):
        # SAL-RULE-002 Stock Reservation
        shortages = []
        for item in self.items.all():
            inventory = Inventory.objects.filter(product=item.product, warehouse=self.warehouse).first()
            if not inventory or inventory.quantity - inventory.reserved_quantity < item.quantity:
                shortages.append(item.product.sku)
        return shortages

    def calculate_shipping_cost(self, total_weight_kg, zone_rate_per_kg):
        # SAL-RULE-003 Shipping Cost Calculation
        return (Decimal(total_weight_kg) * Decimal(zone_rate_per_kg)).quantize(Decimal('0.01'))


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1, validators=[MinValueValidator(Decimal('0.001'))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    @property
    def total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.order.so_id} - {self.product.name}"


class Backorder(models.Model):
    """SAL-RULE-004 Backorder Creation."""

    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='backorders')
    quantity_pending = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])
    created_at = models.DateTimeField(auto_now_add=True)
    fulfilled = models.BooleanField(default=False)

    def __str__(self):
        return f"Backorder for {self.order_item}"


class Delivery(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('failed', 'Failed')]

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='deliveries')
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Delivery for {self.order.so_id}"


class Quotation(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('sent', 'Sent'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('expired', 'Expired')]

    quotation_id = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='quotations')
    valid_until = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    converted_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_quotation')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.quotation_id:
            self.quotation_id = generate_code(Quotation, 'quotation_id', 'QUO')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.quotation_id


class Invoice(models.Model):
    """SAL-RULE-001 Auto Invoice Generation."""

    STATUS_CHOICES = [('draft', 'Draft'), ('issued', 'Issued'), ('paid', 'Paid'), ('overdue', 'Overdue'), ('void', 'Void')]

    invoice_id = models.CharField(max_length=50, unique=True, blank=True)
    order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name='invoice')
    issue_date = models.DateField(default=today)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            self.invoice_id = generate_code(Invoice, 'invoice_id', 'INV')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_id
