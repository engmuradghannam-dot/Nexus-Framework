from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Backorder, Delivery, Invoice, Quotation, SalesOrder, SalesOrderItem


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = '__all__'


class BackorderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Backorder
        fields = '__all__'


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = '__all__'


class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    deliveries = DeliverySerializer(many=True, read_only=True)
    discount_pct = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    requires_discount_approval = serializers.BooleanField(read_only=True)

    class Meta:
        model = SalesOrder
        fields = '__all__'
        read_only_fields = ['so_id']

    def validate(self, attrs):
        customer = attrs.get('customer') or getattr(self.instance, 'customer', None)
        total_amount = attrs.get('total_amount', getattr(self.instance, 'total_amount', 0))
        if customer and customer.exceeds_credit_limit(total_amount):
            raise serializers.ValidationError('Order blocked: customer exceeds credit limit')
        discount_amount = attrs.get('discount_amount', getattr(self.instance, 'discount_amount', 0))
        if total_amount and discount_amount and discount_amount > total_amount * Decimal('0.30'):
            raise serializers.ValidationError('Discount cannot exceed 30% of total amount')

        order_date = attrs.get('order_date', getattr(self.instance, 'order_date', None))
        required_date = attrs.get('required_date', getattr(self.instance, 'required_date', None))
        if order_date and order_date > timezone.now().date():
            raise serializers.ValidationError('Order date cannot be in the future')
        if required_date and order_date and required_date < order_date:
            raise serializers.ValidationError('Required date must be on or after the order date')
        return attrs


class QuotationSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.customer_name', read_only=True)

    class Meta:
        model = Quotation
        fields = '__all__'
        read_only_fields = ['quotation_id']


class InvoiceSerializer(serializers.ModelSerializer):
    order_so_id = serializers.CharField(source='order.so_id', read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['invoice_id']
