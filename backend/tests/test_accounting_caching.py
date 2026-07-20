from datetime import date

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from nexus.apps.accounting.models import Invoice
from nexus.apps.core.models import Branch, Company


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_dashboard_stats_is_cached_per_company_scope():
    company = Company.objects.create(name='Cache Test Co')
    Branch.objects.create(company=company, name='Main')
    user = User.objects.create_user('cacheuser', 'cache@test.com', 'pass', is_superuser=True)
    client = APIClient()
    client.force_authenticate(user=user)

    resp1 = client.get('/api/accounting/invoices/dashboard_stats/', secure=True)
    assert resp1.status_code == 200
    assert resp1.data['total_invoices'] == 0

    # Create an invoice directly (bypassing the API) - a cached response
    # should NOT reflect it yet, since the whole point is not recomputing
    # from every invoice row on every single request.
    Invoice.objects.create(company=company, invoice_type='sales', customer_name='Test Customer',
                            date=date.today(), due_date=date.today(), total=100)

    resp2 = client.get('/api/accounting/invoices/dashboard_stats/', secure=True)
    assert resp2.data['total_invoices'] == 0  # still cached

    cache.clear()

    resp3 = client.get('/api/accounting/invoices/dashboard_stats/', secure=True)
    assert resp3.data['total_invoices'] == 1  # recomputed after cache clear
