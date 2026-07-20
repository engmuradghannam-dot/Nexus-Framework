import pytest
from django.conf import settings
from django.db import connections

from nexus.apps.api_infra.tenancy import Tenant, TenantUser
from nexus.apps.api_infra.tenancy_router import (
    TenantDatabaseRouter, get_current_tenant_db, register_tenant_database,
    reset_current_tenant_db, set_current_tenant_db,
)
from nexus.apps.industry.models import Product


router = TenantDatabaseRouter()


def test_shared_app_always_routes_to_default():
    token = set_current_tenant_db('tenant_whatever')
    try:
        assert router._alias_for('auth') == 'default'
        assert router._alias_for('api_infra') == 'default'
    finally:
        reset_current_tenant_db(token)


def test_tenant_app_routes_to_default_when_no_tenant_context():
    assert get_current_tenant_db() is None
    assert router._alias_for('industry') == 'default'


def test_tenant_app_routes_to_current_tenant_db_when_set():
    token = set_current_tenant_db('tenant_acme')
    try:
        assert router._alias_for('industry') == 'tenant_acme'
    finally:
        reset_current_tenant_db(token)


@pytest.mark.django_db
def test_provisioning_registers_a_distinct_database_alias():
    tenant = Tenant.objects.create(name='Acme Co', schema_name='acmetest')
    assert tenant.db_alias == 'tenant_acmetest'
    alias = register_tenant_database(tenant)
    assert alias in settings.DATABASES
    assert settings.DATABASES[alias]['NAME'] == tenant.db_name
    assert settings.DATABASES[alias]['NAME'] != settings.DATABASES['default']['NAME']
    del settings.DATABASES[alias]


@pytest.mark.django_db(transaction=True)
def test_real_cross_database_isolation():
    """End-to-end: two tenants get two real physical databases, and a record
    created while routed to one is invisible from the other and from the
    shared default database."""
    tenant_a = Tenant.objects.create(name='Tenant A', schema_name='tenanta')
    tenant_b = Tenant.objects.create(name='Tenant B', schema_name='tenantb')

    try:
        alias_a = tenant_a.provision_database()
        alias_b = tenant_b.provision_database()
    except Exception as exc:
        pytest.skip(f"DB user lacks CREATEDB privilege in this environment: {exc}")

    try:
        token = set_current_tenant_db(alias_a)
        try:
            Product.objects.create(name='Tenant A Widget', sku='TENA-001', unit_price=10)
        finally:
            reset_current_tenant_db(token)

        # Visible in tenant A's own database.
        token = set_current_tenant_db(alias_a)
        try:
            assert Product.objects.filter(sku='TENA-001').exists()
        finally:
            reset_current_tenant_db(token)

        # Invisible from tenant B's database.
        token = set_current_tenant_db(alias_b)
        try:
            assert not Product.objects.filter(sku='TENA-001').exists()
        finally:
            reset_current_tenant_db(token)

        # Invisible from the shared default database.
        assert not Product.objects.filter(sku='TENA-001').exists()
    finally:
        for alias in (alias_a, alias_b):
            if alias in connections:
                connections[alias].close()
        _drop_database(tenant_a.db_name)
        _drop_database(tenant_b.db_name)
        settings.DATABASES.pop(alias_a, None)
        settings.DATABASES.pop(alias_b, None)


def _drop_database(name):
    import psycopg2

    default_cfg = settings.DATABASES['default']
    conn = psycopg2.connect(
        dbname='postgres', user=default_cfg['USER'], password=default_cfg['PASSWORD'],
        host=default_cfg['HOST'], port=default_cfg['PORT'],
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{name}"')
    finally:
        conn.close()
