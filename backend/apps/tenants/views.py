from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import Tenant, Domain, TenantUsage
from .serializers import TenantSerializer, TenantCreateSerializer, DomainSerializer, TenantUsageSerializer
from apps.core.mixins import CompanyScopedMixin
from apps.billing.models import Plan, Subscription
from apps.billing.stripe_service import StripeService


class TenantViewSet(viewsets.ModelViewSet):
    """
    Tenant management API.
    Public endpoint for onboarding; restricted for management.
    """
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'create':
            return TenantCreateSerializer
        return TenantSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Onboard new tenant with schema creation and trial setup."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        plan_code = data.pop('plan_code', 'starter')
        admin_email = data.pop('admin_email')
        admin_password = data.pop('admin_password')

        # Generate schema name from slug
        schema_name = data['slug'].lower().replace('-', '_')

        # Create tenant
        tenant = Tenant.objects.create(
            schema_name=schema_name,
            tier='trial',
            status='trial',
            trial_ends_at=timezone.now() + timezone.timedelta(days=14),
            **data
        )

        # Create schema
        tenant.create_schema()

        # Create usage record
        TenantUsage.objects.create(tenant=tenant)

        # Create primary domain
        from django.conf import settings
        platform_domain = getattr(settings, 'SAAS_PLATFORM_DOMAIN', 'nexus-erp.com')
        Domain.objects.create(
            tenant=tenant,
            domain=f"{tenant.slug}.{platform_domain}",
            is_primary=True
        )

        # Set up subscription with plan
        try:
            plan = Plan.objects.get(code=plan_code, is_active=True)
        except Plan.DoesNotExist:
            plan = Plan.objects.filter(is_active=True).first()

        if plan:
            tenant.max_users = plan.max_users
            tenant.max_warehouses = plan.max_warehouses
            tenant.max_branches = plan.max_branches
            tenant.storage_limit_mb = plan.storage_limit_gb * 1024
            tenant.enabled_modules = list(plan.enabled_modules or [])
            tenant.save()

            # Create Stripe subscription
            stripe_service = StripeService()
            stripe_service.create_subscription(tenant, plan)

        # Create admin user in tenant schema
        # This would be done via a signal or management command

        response_serializer = TenantSerializer(tenant, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def suspend(self, request, slug=None):
        """Suspend a tenant."""
        tenant = self.get_object()
        tenant.status = 'suspended'
        tenant.save()
        return Response({'status': 'suspended'})

    @action(detail=True, methods=['post'])
    def activate(self, request, slug=None):
        """Activate a tenant."""
        tenant = self.get_object()
        tenant.status = 'active'
        tenant.activated_at = timezone.now()
        tenant.save()
        return Response({'status': 'activated'})

    @action(detail=True, methods=['get'])
    def usage(self, request, slug=None):
        """Get tenant usage statistics."""
        tenant = self.get_object()
        try:
            usage = tenant.usage
            serializer = TenantUsageSerializer(usage)
            return Response(serializer.data)
        except TenantUsage.DoesNotExist:
            return Response({'error': 'Usage record not found'}, status=404)


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAdminUser]
