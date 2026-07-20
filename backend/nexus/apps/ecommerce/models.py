from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from nexus.apps.core.models import Company, Branch, Warehouse
from nexus.apps.core.utils import generate_code
from nexus.apps.core.validators import phone_validator
from nexus.apps.industry.models import Product

class ProductCatalog(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='catalog')
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_featured = models.BooleanField(default=False)
    is_online = models.BooleanField(default=True)
    images = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Catalog: {self.product.name}"

class Customer(models.Model):
    TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
    ]

    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True, validators=[phone_validator])
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='individual')
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('converted', 'Converted'),
        ('abandoned', 'Abandoned'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart #{self.id}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    class Meta:
        unique_together = ['cart', 'product']

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=50, unique=True, blank=True)  # SO-YYYY-#####
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    shipping_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_code(Order, 'order_number', 'SO')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class POSession(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('reconciled', 'Reconciled'),
    ]

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='pos_sessions')
    cashier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pos_sessions', db_constraint=False)
    opening_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    closing_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-opened_at']

    def __str__(self):
        return f"POS #{self.id} - {self.branch.name}"

class POSTransaction(models.Model):
    TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('refund', 'Refund'),
        ('void', 'Void'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('digital', 'Digital Wallet'),
    ]

    session = models.ForeignKey(POSession, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='sale')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TXN-{self.id}"

class POSTransactionItem(models.Model):
    transaction = models.ForeignKey(POSTransaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
