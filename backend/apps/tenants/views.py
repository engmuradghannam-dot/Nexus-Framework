from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django_tenants.utils import schema_context
from .models import Tenant, Domain, TenantUser, TenantUsage
from .serializers import (
    TenantSerializer, TenantCreateSerializer, TenantUserSerializer,
    DomainSerializer, TenantUsageSerializer
)
from apps.billing.models import Plan, Subscription
from apps.billing.stripe_service import StripeService


class TenantViewSet(viewsets.ModelViewSet):
    """Tenant management with django-tenants schema creation."""
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
        """Onboard new tenant with automatic schema creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        plan_code = data.pop('plan_code', 'starter')
        admin_email = data.pop('admin_email')
        admin_password = data.pop('admin_password')

        # Create tenant (schema auto-created by django-tenants)
        tenant = Tenant.objects.create(
            tier='trial',
            trial_ends_at=timezone.now() + timezone.timedelta(days=14),
            **data
        )

        # Create primary domain
        from django.conf import settings
        platform_domain = getattr(settings, 'PLATFORM_DOMAIN', 'nexus-erp.com')
        Domain.objects.create(
            tenant=tenant,
            domain=f"{tenant.slug}.{platform_domain}",
            is_primary=True
        )

        # Create usage record
        TenantUsage.objects.create(tenant=tenant)

        # Set up plan limits
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

        # Create admin user in public schema (global auth)
        admin_user = TenantUser.objects.create_user(
            email=admin_email,
            password=admin_password,
            first_name='Admin',
        )
        admin_user.tenants.add(tenant)
        admin_user.current_tenant = tenant
        admin_user.save()

        # Create admin user in tenant schema
        with schema_context(tenant.schema_name):
            from apps.core.models import User
            User.objects.create_user(
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                role='Admin',
                company=None,  # Will be set via signal
            )

        response_serializer = TenantSerializer(tenant, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def switch(self, request, slug=None):
        """Switch current tenant for authenticated user."""
        tenant = self.get_object()
        user = request.user

        if not user.tenants.filter(id=tenant.id).exists() and not user.is_superuser:
            return Response({'error': 'Not a member of this tenant'}, status=403)

        user.current_tenant = tenant
        user.save()

        return Response({
            'tenant': TenantSerializer(tenant).data,
            'redirect_url': f"https://{tenant.domains.filter(is_primary=True).first().domain}"
        })


class TenantUserViewSet(viewsets.ModelViewSet):
    """Global user management across tenants."""
    queryset = TenantUser.objects.all()
    serializer_class = TenantUserSerializer
    permission_classes = [permissions.IsAdminUser]
