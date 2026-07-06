from rest_framework import serializers
from .models import Plan, Subscription, Invoice, Payment, UsageRecord


class PlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'code', 'description', 'tier', 'price_monthly',
            'price_yearly', 'currency', 'billing_interval', 'max_users',
            'max_warehouses', 'max_branches', 'storage_limit_gb',
            'includes_api_access', 'includes_advanced_reporting',
            'includes_ai_features', 'includes_white_label',
            'enabled_modules', 'features', 'is_public', 'sort_order',
        ]

    def get_features(self, obj):
        features = []
        if obj.includes_api_access:
            features.append('api_access')
        if obj.includes_advanced_reporting:
            features.append('advanced_reporting')
        if obj.includes_ai_features:
            features.append('ai_features')
        if obj.includes_white_label:
            features.append('white_label')
        return features


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    days_until_renewal = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'status', 'current_period_start', 'current_period_end',
            'trial_start', 'trial_end', 'cancel_at_period_end', 'canceled_at',
            'days_until_renewal', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'stripe_subscription_id', 'stripe_customer_id', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'status', 'subtotal', 'tax_percent',
            'tax_amount', 'total', 'amount_paid', 'amount_due', 'currency',
            'description', 'due_date', 'paid_at', 'pdf_url', 'created_at',
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'status', 'payment_method',
            'card_last4', 'card_brand', 'failure_message', 'refunded_amount',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CheckoutSessionSerializer(serializers.Serializer):
    """Serializer for creating Stripe checkout session."""
    plan_id = serializers.UUIDField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    billing_interval = serializers.ChoiceField(choices=['month', 'year'], default='month')
