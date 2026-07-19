"""Database-per-tenant routing.

Each tenant that has its own database_url gets its data in a separate physical
database, registered as a Django connection at runtime and selected per request.
Tenants without a database_url fall back to the shared 'default' database, so
adoption is gradual — you move one tenant to its own database without touching
the rest.

Three pieces:
  - register_tenant_db(tenant): add the tenant's database to Django's connection
    registry if it isn't there yet.
  - a thread-local current-tenant context, set by middleware per request.
  - TenantRouter: routes reads/writes to the current tenant's alias.

Safety notes: shared apps (the tenant registry itself, sessions, contenttypes,
auth) must stay in 'default' — a tenant DB can't hold the table that lists
tenants. allow_migrate keeps those out of tenant databases.
"""
import threading

from django.conf import settings
from django.db import connections

_local = threading.local()

# Apps whose tables live only in the shared default database, never in a
# per-tenant one. The tenant registry can't live inside a tenant DB, and auth /
# sessions / contenttypes are cross-tenant infrastructure.
SHARED_APPS = {"tenants", "sessions", "contenttypes", "admin", "auth"}


def set_current_tenant(tenant):
    _local.tenant = tenant
    if tenant is not None:
        register_tenant_db(tenant)


def get_current_tenant():
    return getattr(_local, "tenant", None)


def clear_current_tenant():
    _local.tenant = None


def current_db_alias():
    tenant = get_current_tenant()
    return tenant.db_alias if tenant is not None else "default"


def register_tenant_db(tenant):
    """Ensure the tenant's database is in Django's connection registry.

    Idempotent: registering an alias that's already present is a no-op. Uses the
    default database's settings as the template, overriding only the connection
    details parsed from the tenant's database_url.
    """
    if not getattr(tenant, "database_url", ""):
        return "default"
    alias = tenant.db_alias
    if alias in connections.databases:
        return alias

    import dj_database_url

    base = dict(settings.DATABASES["default"])
    parsed = dj_database_url.parse(tenant.database_url, conn_max_age=600)
    base.update(parsed)
    connections.databases[alias] = base
    return alias


class TenantRouter:
    """Route ORM operations to the current tenant's database.

    Shared-app models always resolve to 'default'. Everything else follows the
    tenant set for the current request; with no tenant (management commands, the
    shared default tenant) that's also 'default', so nothing breaks when the
    feature is unused.
    """

    def _db_for(self, model):
        if model._meta.app_label in SHARED_APPS:
            return "default"
        return current_db_alias()

    def db_for_read(self, model, **hints):
        return self._db_for(model)

    def db_for_write(self, model, **hints):
        return self._db_for(model)

    def allow_relation(self, obj1, obj2, **hints):
        # Relations are fine within one database; cross-db relations aren't
        # created by the ORM, so allow and let the DB enforce integrity.
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Shared apps migrate only on default; tenant databases get everything
        # else. On 'default' we allow all, so the shared DB is a full schema too
        # (it's the fallback for tenants without their own database).
        if app_label in SHARED_APPS:
            return db == "default"
        return True
