from django.db import models
from django.contrib.auth.models import User
from django.db import connection
from django_tenants.models import TenantMixin, DomainMixin
from django_tenants.utils import schema_context
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class Tenant(TenantMixin):
    """Multi-tenant schema model"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schema_name = models.CharField(max_length=63, unique=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    plan = models.CharField(max_length=50, default='free')
    auto_create_schema = True
    auto_drop_schema = True

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

class Domain(DomainMixin):
    """Domain routing for tenants"""
    pass

class TenantUser(models.Model):
    """Link users to tenants with roles"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
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


class TenantViewSet(viewsets.ModelViewSet):
    """Tenant management"""
    queryset = Tenant.objects.all()
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save()
        return Response({"status": "activated"})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save()
        return Response({"status": "deactivated"})

    @action(detail=True, methods=['post'])
    def switch_schema(self, request, pk=None):
        """Switch to tenant schema for current request"""
        tenant = self.get_object()
        with schema_context(tenant.schema_name):
            # Test connection
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [tenant.schema_name])
            exists = cursor.fetchone()
            return Response({
                "tenant": tenant.name,
                "schema": tenant.schema_name,
                "schema_exists": bool(exists),
                "current_schema": connection.schema_name
            })

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        tenant = self.get_object()
        with schema_context(tenant.schema_name):
            from nexus.apps.core.models import Company
            from nexus.apps.hr.models import Employee
            from nexus.apps.pmo.models import Project
            from nexus.apps.accounting.models import Invoice

            return Response({
                "tenant": tenant.name,
                "companies": Company.objects.count(),
                "employees": Employee.objects.count(),
                "projects": Project.objects.count(),
                "invoices": Invoice.objects.count(),
                "users": tenant.users.count()
            })

    @action(detail=False, methods=['post'])
    def create_tenant(self, request):
        """Create new tenant with schema"""
        name = request.data.get('name')
        schema = request.data.get('schema_name')

        if Tenant.objects.filter(schema_name=schema).exists():
            return Response({"error": "Schema already exists"}, status=status.HTTP_400_BAD_REQUEST)

        tenant = Tenant.objects.create(
            name=name,
            schema_name=schema,
            plan=request.data.get('plan', 'free')
        )

        # Create domain
        Domain.objects.create(
            tenant=tenant,
            domain=f"{schema}.nexus.local",
            is_primary=True
        )

        return Response({
            "status": "created",
            "tenant_id": tenant.id,
            "schema": tenant.schema_name,
            "domain": f"{schema}.nexus.local"
        })

class TenantUserViewSet(viewsets.ModelViewSet):
    """Tenant user management"""
    queryset = TenantUser.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def my_tenants(self, request):
        tenants = TenantUser.objects.filter(user=request.user, is_active=True)
        return Response([{
            "tenant_id": t.tenant.id,
            "tenant_name": t.tenant.name,
            "role": t.role,
            "joined_at": t.joined_at
        } for t in tenants])

    @action(detail=False, methods=['post'])
    def invite(self, request):
        tenant_id = request.data.get('tenant_id')
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'user')

        try:
            tenant = Tenant.objects.get(id=tenant_id)
            user = User.objects.get(id=user_id)

            # Check if inviter is owner/admin
            inviter = TenantUser.objects.filter(tenant=tenant, user=request.user, role__in=['owner', 'admin']).first()
            if not inviter:
                return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

            tu, created = TenantUser.objects.get_or_create(
                tenant=tenant,
                user=user,
                defaults={'role': role}
            )

            return Response({
                "status": "invited" if created else "already_member",
                "user": user.username,
                "role": role
            })
        except Tenant.DoesNotExist:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


# Middleware for tenant detection
class TenantMiddleware:
    """Detect tenant from subdomain or header"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get tenant from subdomain
        host = request.get_host()
        subdomain = host.split('.')[0]

        # Or from header
        tenant_header = request.META.get('HTTP_X_TENANT')

        tenant_identifier = tenant_header or subdomain

        if tenant_identifier and tenant_identifier != 'www':
            try:
                tenant = Tenant.objects.get(schema_name=tenant_identifier, is_active=True)
                request.tenant = tenant
                connection.set_tenant(tenant)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None

        response = self.get_response(request)
        return response
