from rest_framework import serializers
from .models import Tenant, Domain, TenantUsage


class TenantSerializer(serializers.ModelSerializer):
    usage = serializers.SerializerMethodField()
    domains = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'schema_name', 'tier', 'status',
            'trial_ends_at', 'max_users', 'max_warehouses', 'max_branches',
            'storage_limit_mb', 'enabled_modules', 'email', 'phone',
            'address', 'country', 'timezone', 'logo_url', 'primary_color',
            'created_at', 'updated_at', 'usage', 'domains', 'is_active',
        ]
        read_only_fields = ['id', 'schema_name', 'stripe_customer_id', 'stripe_subscription_id', 'created_at', 'updated_at']

    def get_usage(self, obj):
        try:
            usage = obj.usage
            return {
                'current_users': usage.current_users,
                'current_warehouses': usage.current_warehouses,
                'current_branches': usage.current_branches,
                'storage_used_mb': usage.storage_used_mb,
                'api_calls_this_month': usage.api_calls_this_month,
                'documents_generated_this_month': usage.documents_generated_this_month,
            }
        except TenantUsage.DoesNotExist:
            return None

    def get_domains(self, obj):
        return [{'domain': d.domain, 'is_primary': d.is_primary} for d in obj.domains.all()]


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for tenant onboarding."""
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)
    plan_code = serializers.CharField(write_only=True, required=False, default='starter')

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'email', 'phone', 'country', 'timezone',
                  'admin_email', 'admin_password', 'plan_code']

    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This subdomain is already taken.")
        return value


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary', 'ssl_enabled', 'created_at']
        read_only_fields = ['id', 'created_at']


class TenantUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantUsage
        fields = ['current_users', 'current_warehouses', 'current_branches',
                  'storage_used_mb', 'api_calls_this_month', 'documents_generated_this_month']
