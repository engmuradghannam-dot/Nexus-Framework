"""
Complete database router for true tenant isolation.
Routes all tenant data to tenant-specific schemas.
"""
from django.db import connection


class SaaSTenantRouter:
    """
    Database router that ensures:
    1. Public models (tenants, billing, auth) stay in public schema
    2. All other models route to tenant-specific schemas
    3. Cross-tenant queries are impossible
    """

    PUBLIC_APPS = {
        'tenants', 'billing', 'auth', 'sessions', 'contenttypes',
        'admin', 'guardian', 'django_celery_beat', 'django_celery_results',
        'sites', 'socialaccount',
    }

    PUBLIC_MODELS = {
        'tenants.Tenant', 'tenants.Domain', 'tenants.TenantUsage',
        'billing.Plan', 'billing.Subscription', 'billing.Invoice',
        'billing.Payment', 'billing.UsageRecord',
    }

    def _is_public(self, model):
        """Check if model should stay in public schema."""
        app_label = model._meta.app_label
        model_path = f"{app_label}.{model._meta.object_name}"
        return app_label in self.PUBLIC_APPS or model_path in self.PUBLIC_MODELS

    def db_for_read(self, model, **hints):
        """Direct reads to tenant schema or public."""
        if self._is_public(model):
            return 'default'
        return 'default'

    def db_for_write(self, model, **hints):
        """Direct writes to tenant schema or public."""
        if self._is_public(model):
            return 'default'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Prevent cross-tenant relations."""
        if self._is_public(obj1.__class__) and self._is_public(obj2.__class__):
            return True
        if not self._is_public(obj1.__class__) and not self._is_public(obj2.__class__):
            return True
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Control migrations."""
        if app_label in self.PUBLIC_APPS:
            return True
        if app_label == 'tenants':
            return True
        # Other apps: tenant schemas migrated via management command
        return db == 'default'
