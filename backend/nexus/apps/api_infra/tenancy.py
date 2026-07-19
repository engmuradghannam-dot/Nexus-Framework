"""
Tenancy — lightweight, FK/membership based.

Previously this imported django_tenants (TenantMixin/DomainMixin, schema_context,
connection.set_tenant) but the project was NEVER configured for it (no
TENANT_MODEL, SHARED_APPS/TENANT_APPS, or DB router), so the app crashed on
boot. Every domain model already isolates by a `company` FK, so tenancy here is
plain models + membership; data isolation is enforced by
`nexus.apps.api_infra.scoping.CompanyScopedViewSet`.

If you later want true schema-per-tenant isolation, re-introduce django_tenants
deliberately and configure it end-to-end — don't leave it half-wired.
"""
from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from nexus.apps.core.validators import alphanumeric_validator


class Tenant(models.Model):
    """A customer workspace. `schema_name` is kept as a stable slug identifier."""
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True)
    schema_name = models.CharField(max_length=63, unique=True, validators=[alphanumeric_validator])
    is_active = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    plan = models.CharField(max_length=50, default='free')

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(models.Model):
    """Domain routing for tenants."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=True)

    def __str__(self):
        return self.domain


class TenantUser(models.Model):
    """Link users to tenants with roles."""
    ROLE_CHOICES = [
        ('owner', 'Owner'), ('admin', 'Admin'),
        ('manager', 'Manager'), ('user', 'User'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenants')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['tenant', 'user']

    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name}"


def user_is_member(user, tenant):
    if not (user and user.is_authenticated):
        return False
    if user.is_superuser:
        return True
    return TenantUser.objects.filter(tenant=tenant, user=user, is_active=True).exists()


class TenantViewSet(viewsets.ModelViewSet):
    """Tenant management — admin only."""
    queryset = Tenant.objects.all()
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save(update_fields=['is_active'])
        return Response({"status": "activated"})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save(update_fields=['is_active'])
        return Response({"status": "deactivated"})

    @action(detail=False, methods=['post'])
    def create_tenant(self, request):
        name = request.data.get('name')
        schema = request.data.get('schema_name')
        if not name or not schema:
            return Response({"error": "name and schema_name required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if Tenant.objects.filter(schema_name=schema).exists():
            return Response({"error": "Schema already exists"},
                            status=status.HTTP_400_BAD_REQUEST)
        tenant = Tenant.objects.create(
            name=name, schema_name=schema, plan=request.data.get('plan', 'free'))
        Domain.objects.create(tenant=tenant, domain=f"{schema}.nexus.local", is_primary=True)
        return Response({"status": "created", "tenant_id": tenant.id,
                         "schema": tenant.schema_name}, status=status.HTTP_201_CREATED)


class TenantUserViewSet(viewsets.ModelViewSet):
    """Tenant membership management."""
    queryset = TenantUser.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A user only sees memberships of tenants they belong to.
        if self.request.user.is_superuser:
            return TenantUser.objects.all()
        my_tenants = TenantUser.objects.filter(
            user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
        return TenantUser.objects.filter(tenant_id__in=my_tenants)

    @action(detail=False, methods=['get'])
    def my_tenants(self, request):
        tenants = TenantUser.objects.filter(user=request.user, is_active=True)
        return Response([{
            "tenant_id": t.tenant.id, "tenant_name": t.tenant.name,
            "role": t.role, "joined_at": t.joined_at,
        } for t in tenants])

    @action(detail=False, methods=['post'])
    def invite(self, request):
        tenant_id = request.data.get('tenant_id')
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'user')
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            user = User.objects.get(id=user_id)
        except Tenant.DoesNotExist:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Only an owner/admin of THIS tenant can invite.
        inviter = TenantUser.objects.filter(
            tenant=tenant, user=request.user, role__in=['owner', 'admin'], is_active=True).first()
        if not (request.user.is_superuser or inviter):
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        tu, created = TenantUser.objects.get_or_create(
            tenant=tenant, user=user, defaults={'role': role})
        return Response({"status": "invited" if created else "already_member",
                         "user": user.username, "role": role})


class TenantMiddleware:
    """Attach request.tenant from subdomain or X-Tenant header — but ONLY if the
    authenticated caller is a verified member. Never trust the header alone."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        host = request.get_host()
        subdomain = host.split('.')[0]
        identifier = request.META.get('HTTP_X_TENANT') or subdomain

        if identifier and identifier != 'www':
            try:
                tenant = Tenant.objects.get(schema_name=identifier, is_active=True)
            except Tenant.DoesNotExist:
                tenant = None
            if tenant is not None and user_is_member(getattr(request, 'user', None), tenant):
                request.tenant = tenant

        return self.get_response(request)
