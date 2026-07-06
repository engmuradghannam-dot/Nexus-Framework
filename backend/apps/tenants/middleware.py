"""
Tenant resolution middleware for django-tenants.
"""
from django.db import connection
from django.http import JsonResponse
from django.core.cache import cache
from django_tenants.utils import get_tenant_model


class TenantResolutionMiddleware:
    """
    Middleware that resolves tenant from request host (subdomain or custom domain).
    Works with django-tenants TenantMainMiddleware.
    """
    TENANT_NOT_FOUND = {"error": "Tenant not found", "code": "TENANT_NOT_FOUND"}
    TENANT_SUSPENDED = {"error": "Tenant suspended", "code": "TENANT_SUSPENDED"}
    TENANT_EXPIRED = {"error": "Trial expired", "code": "TRIAL_EXPIRED"}

    PUBLIC_PATHS = [
        '/admin/', '/api/v1/tenants/', '/api/v1/auth/register/',
        '/api/v1/auth/login/', '/api/v1/auth/refresh/',
        '/api/v1/billing/webhook/', '/static/', '/media/',
        '/health', '/metrics', '/api/v1/plans/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.TenantModel = get_tenant_model()

    def __call__(self, request):
        if self._is_public_path(request.path):
            return self.get_response(request)

        host = request.get_host().split(':')[0]

        # Try cache first
        cache_key = f"tenant:{host}"
        tenant_data = cache.get(cache_key)

        if not tenant_data:
            tenant = self._resolve_tenant(host)
            if isinstance(tenant, dict):
                return JsonResponse(tenant, status=403)

            tenant_data = {
                'id': str(tenant.id),
                'schema_name': tenant.schema_name,
                'name': tenant.name,
                'tier': tenant.tier,
                'enabled_modules': tenant.enabled_modules or [],
            }
            cache.set(cache_key, tenant_data, 300)

        # Check module access for API paths
        if request.path.startswith('/api/v1/'):
            module_code = self._extract_module(request.path)
            if module_code and module_code not in tenant_data['enabled_modules']:
                return JsonResponse({"error": "Module not enabled", "code": "MODULE_DISABLED"}, status=403)

        request.tenant = tenant_data
        response = self.get_response(request)
        return response

    def _resolve_tenant(self, host):
        """Resolve tenant from host."""
        try:
            from apps.tenants.models import Domain
            domain = Domain.objects.select_related('tenant').get(domain=host)
            return domain.tenant
        except Domain.DoesNotExist:
            pass

        parts = host.split('.')
        if len(parts) >= 3:
            slug = parts[0]
            try:
                return self.TenantModel.objects.get(slug=slug)
            except self.TenantModel.DoesNotExist:
                pass

        if host in ('localhost', '127.0.0.1', 'nexus-erp.local'):
            try:
                return self.TenantModel.objects.get(schema_name='public')
            except self.TenantModel.DoesNotExist:
                return self.TENANT_NOT_FOUND

        return self.TENANT_NOT_FOUND

    def _is_public_path(self, path):
        return any(path.startswith(p) for p in self.PUBLIC_PATHS)

    def _extract_module(self, path):
        parts = path.replace('/api/v1/', '').split('/')
        if parts:
            module_map = {
                'accounts': 'accounts', 'inventory': 'inventory',
                'buying': 'buying', 'selling': 'selling',
                'manufacturing': 'manufacturing', 'hr': 'hr',
                'crm': 'crm', 'projects': 'projects',
                'assets': 'assets', 'workflow': 'workflow',
            }
            return module_map.get(parts[0])
        return None
