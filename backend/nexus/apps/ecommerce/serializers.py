from rest_framework import serializers
from .models import (
    ProductCatalog, Customer, Cart, CartItem, Order, OrderItem,
    POSession, POSTransaction, POSTransactionItem
)

class ProductCatalogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = ProductCatalog
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number']

class POSTransactionItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = POSTransactionItem
        fields = '__all__'

class POSTransactionSerializer(serializers.ModelSerializer):
    items = POSTransactionItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)

    class Meta:
        model = POSTransaction
        fields = '__all__'

class POSessionSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    transaction_count = serializers.IntegerField(source='transactions.count', read_only=True)
    total_sales = serializers.SerializerMethodField()

    class Meta:
        model = POSession
        fields = '__all__'

    def get_total_sales(self, obj):
        return sum(t.total for t in obj.transactions.filter(type='sale'))
