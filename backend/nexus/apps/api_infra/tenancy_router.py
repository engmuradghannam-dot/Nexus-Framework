"""
True database-per-tenant routing.

Control-plane apps (auth, contenttypes, sessions, admin, api_infra, audit)
always live in the `default` database - this is where the Tenant directory
itself lives, so it must be resolvable before we know which tenant a request
belongs to, and it's where the cross-tenant audit trail is centralized for
platform admins.

Every other app (core, hr, accounting, industry, crm, sales, pmo,
manufacturing, workflow, permissions, ecommerce, regulatory, ai_module) is
tenant-scoped: its tables are migrated into `default` (so existing tests and
non-tenant/dev usage keep working untouched) AND into each tenant's own
physical database. A request bound to a tenant (via TenantMiddleware) reads
and writes that tenant's database instead of `default` for the duration of
the request.

Known constraint: a queryset on a tenant-scoped model must not
select_related() across the boundary into a control-plane model (e.g. `user`,
a raw auth.User FK) - Django compiles that as a single SQL JOIN against one
connection, and the control-plane tables don't exist in tenant databases.
Plain (non-joined) FK access is unaffected, since each access is routed
independently through this router.
"""
import contextvars

SHARED_APPS = {
    'admin', 'auth', 'contenttypes', 'sessions', 'api_infra', 'audit',
}

_current_tenant_db = contextvars.ContextVar('current_tenant_db', default=None)


def get_current_tenant_db():
    return _current_tenant_db.get()


def set_current_tenant_db(alias):
    return _current_tenant_db.set(alias)


def reset_current_tenant_db(token):
    _current_tenant_db.reset(token)


def register_tenant_database(tenant):
    """Idempotently add this tenant's database connection to Django's registry."""
    from django.conf import settings

    alias = tenant.db_alias
    if alias not in settings.DATABASES:
        base = dict(settings.DATABASES['default'])
        base['NAME'] = tenant.db_name
        settings.DATABASES[alias] = base
    return alias


class TenantDatabaseRouter:
    def _alias_for(self, app_label):
        if app_label in SHARED_APPS:
            return 'default'
        return get_current_tenant_db() or 'default'

    def db_for_read(self, model, **hints):
        return self._alias_for(model._meta.app_label)

    def db_for_write(self, model, **hints):
        return self._alias_for(model._meta.app_label)

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in SHARED_APPS:
            return db == 'default'
        # Tenant-scoped apps: keep migrating into `default` (dev/tests/legacy
        # single-DB usage) as well as into any provisioned tenant_* database.
        return db == 'default' or db.startswith('tenant_')
