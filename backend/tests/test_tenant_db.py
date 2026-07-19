"""Database-per-tenant routing.

A tenant with its own database_url gets a dedicated database, selected per
request; a tenant without one falls back to the shared default database, so
per-tenant databases are adopted gradually. Shared apps (the tenant registry,
auth, sessions) always stay in default.
"""
import pytest

from apps.buying.models import PurchaseOrder
from apps.tenants.models import Tenant
from apps.tenants.routing import (
    SHARED_APPS, TenantRouter, clear_current_tenant, current_db_alias,
    register_tenant_db, set_current_tenant,
)


@pytest.fixture(autouse=True)
def _clear():
    clear_current_tenant()
    yield
    clear_current_tenant()


@pytest.mark.django_db
class TestDbAlias:
    def test_tenant_without_url_uses_default(self):
        t = Tenant.objects.create(name="S", slug="s", subdomain="s")
        assert t.db_alias == "default"

    def test_tenant_with_url_gets_own_alias(self):
        t = Tenant.objects.create(name="O", slug="o", subdomain="o",
                                  database_url="sqlite:////tmp/t_own.db")
        assert t.db_alias == f"tenant_{t.pk}"


@pytest.mark.django_db
class TestRouter:
    def setup_method(self):
        self.router = TenantRouter()

    def test_no_tenant_routes_to_default(self):
        clear_current_tenant()
        assert self.router.db_for_read(PurchaseOrder) == "default"

    def test_shared_tenant_routes_to_default(self):
        t = Tenant.objects.create(name="S", slug="s", subdomain="s")
        set_current_tenant(t)
        assert self.router.db_for_read(PurchaseOrder) == "default"

    def test_dedicated_tenant_routes_to_its_alias(self):
        t = Tenant.objects.create(name="O", slug="o", subdomain="o",
                                  database_url="sqlite:////tmp/t_own.db")
        set_current_tenant(t)
        assert self.router.db_for_write(PurchaseOrder) == f"tenant_{t.pk}"

    def test_shared_apps_always_route_to_default(self):
        t = Tenant.objects.create(name="O", slug="o", subdomain="o",
                                  database_url="sqlite:////tmp/t_own.db")
        set_current_tenant(t)
        # Even with a dedicated tenant active, the Tenant model stays in default.
        assert self.router.db_for_read(Tenant) == "default"

    def test_allow_migrate_keeps_shared_apps_off_tenant_dbs(self):
        assert self.router.allow_migrate("default", "tenants") is True
        assert self.router.allow_migrate("tenant_5", "tenants") is False
        assert self.router.allow_migrate("tenant_5", "buying") is True


@pytest.mark.django_db
class TestRegistration:
    def test_register_is_idempotent(self):
        t = Tenant.objects.create(name="O", slug="o", subdomain="o",
                                  database_url="sqlite:////tmp/t_own.db")
        assert register_tenant_db(t) == register_tenant_db(t)

    def test_shared_tenant_registration_is_noop(self):
        t = Tenant.objects.create(name="S", slug="s", subdomain="s")
        assert register_tenant_db(t) == "default"
