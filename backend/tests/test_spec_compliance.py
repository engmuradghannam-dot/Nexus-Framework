"""Tests for the ERP_Complete_System.xlsx rules/controls implemented so far.

Each test names the spec ID it covers so the sheet can be traced to code.
"""
from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry
from apps.selling.models import Customer, SalesOrder, SalesOrderItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="spec@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Spec Co", code="SPEC-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="Riyadh", code="RUH", address="Riyadh")


@pytest.fixture
def item(company):
    return Item.objects.create(
        company=company, item_code="SPEC-1", item_name="Widget", standard_rate=100
    )


@pytest.mark.django_db
class TestBranchRules:
    def test_brn_rule_001_new_branch_gets_default_warehouse(self, company):
        b = Branch.objects.create(company=company, name="Jeddah", code="JED", address="Jeddah")
        assert Warehouse.objects.filter(branch=b).count() == 1
        assert Warehouse.objects.get(branch=b).code == "JED-WH"

    def test_brn_rule_002_only_one_head_office_per_company(self, company):
        Branch.objects.create(
            company=company, name="HQ", code="HQ", address="Riyadh", branch_type="Head Office"
        )
        with pytest.raises(ValidationError):
            Branch.objects.create(
                company=company, name="HQ2", code="HQ2", address="Jeddah",
                branch_type="Head Office",
            )

    def test_brn_rule_002_second_company_may_have_its_own_head_office(self, company):
        Branch.objects.create(
            company=company, name="HQ", code="HQ", address="Riyadh", branch_type="Head Office"
        )
        other = CompanyProfile.objects.create(name="Other Co", code="OTHER-CO")
        b = Branch.objects.create(
            company=other, name="HQ", code="HQ-O", address="Dammam", branch_type="Head Office"
        )
        assert b.pk

    def test_brn_rule_002_ordinary_branches_are_unlimited(self, company):
        Branch.objects.create(company=company, name="B1", code="B1", address="Riyadh")
        b = Branch.objects.create(company=company, name="B2", code="B2", address="Jeddah")
        assert b.pk

    def test_brn_rule_005_close_time_must_be_after_open_time(self, company):
        with pytest.raises(ValidationError):
            Branch.objects.create(
                company=company, name="Bad Hours", code="BH", address="Riyadh",
                open_time=time(17, 0), close_time=time(9, 0),
            )

    def test_brn_rule_005_valid_hours_accepted(self, company):
        b = Branch.objects.create(
            company=company, name="Good Hours", code="GH", address="Riyadh",
            open_time=time(9, 0), close_time=time(17, 0),
        )
        assert b.pk

    def test_brn_rule_004_haversine_distance(self, company):
        ruh = Branch.objects.create(
            company=company, name="Riyadh", code="R1", address="Riyadh",
            latitude=Decimal("24.7136"), longitude=Decimal("46.6753"),
        )
        jed = Branch.objects.create(
            company=company, name="Jeddah", code="J1", address="Jeddah",
            latitude=Decimal("21.4858"), longitude=Decimal("39.1925"),
        )
        # Riyadh -> Jeddah great-circle is ~845 km
        assert 830 < ruh.distance_to(jed) < 860

    def test_brn_rule_004_distance_is_none_without_coordinates(self, company, branch):
        other = Branch.objects.create(company=company, name="NoGeo", code="NG", address="X")
        assert branch.distance_to(other) is None

    def test_brn_ctrl_005_license_expiry_alert_within_60_days(self, company):
        soon = Branch.objects.create(
            company=company, name="Expiring", code="EX", address="Riyadh",
            license_expiry=date.today() + timedelta(days=30),
        )
        later = Branch.objects.create(
            company=company, name="Fine", code="FN", address="Riyadh",
            license_expiry=date.today() + timedelta(days=200),
        )
        assert soon.license_expires_soon is True
        assert later.license_expires_soon is False
        assert Branch.objects.get(pk=company.branches.first().pk).license_expires_soon in (True, False)


@pytest.mark.django_db
class TestStockIsPerWarehouse:
    """SAL-CTRL-002 / WHS-CTRL-001: availability is a per-location question."""

    def test_stock_in_warehouse_is_scoped_to_that_warehouse(self, company, branch, item):
        wh_a = Warehouse.objects.get(branch=branch)
        wh_b = Warehouse.objects.create(branch=branch, name="Second", code="WH-B")
        StockEntry.objects.create(
            company=company, warehouse=wh_a, item=item, entry_type="Receipt", quantity=10, rate=100
        )
        assert item.stock_in_warehouse(wh_a) == 10
        assert item.stock_in_warehouse(wh_b) == 0
        assert item.stock_quantity == 10  # company-wide total unchanged

    def test_issue_reduces_only_its_own_warehouse(self, company, branch, item):
        wh_a = Warehouse.objects.get(branch=branch)
        StockEntry.objects.create(
            company=company, warehouse=wh_a, item=item, entry_type="Receipt", quantity=10, rate=100
        )
        StockEntry.objects.create(
            company=company, warehouse=wh_a, item=item, entry_type="Issue", quantity=4, rate=100
        )
        assert item.stock_in_warehouse(wh_a) == 6

    def test_cannot_deliver_from_a_warehouse_that_has_no_stock(self, company, branch, item):
        """The bug this fixes: stock sat in warehouse B, the order shipped from
        warehouse A, and the global total made it look available."""
        wh_a = Warehouse.objects.get(branch=branch)
        wh_b = Warehouse.objects.create(branch=branch, name="Second", code="WH-B")
        StockEntry.objects.create(
            company=company, warehouse=wh_b, item=item, entry_type="Receipt", quantity=50, rate=100
        )
        customer = Customer.objects.create(company=company, name="Client")
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-WH-1",
            transaction_date=date.today(), branch=branch, warehouse=wh_a, status="Submitted",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=5, rate=100)
        with pytest.raises(ValidationError, match="Insufficient stock"):
            so.deliver_stock()

    def test_delivers_when_the_right_warehouse_holds_the_stock(self, company, branch, item):
        wh_a = Warehouse.objects.get(branch=branch)
        StockEntry.objects.create(
            company=company, warehouse=wh_a, item=item, entry_type="Receipt", quantity=50, rate=100
        )
        customer = Customer.objects.create(company=company, name="Client")
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-WH-2",
            transaction_date=date.today(), branch=branch, warehouse=wh_a, status="Submitted",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=5, rate=100)
        so.deliver_stock()
        assert item.stock_in_warehouse(wh_a) == 45


@pytest.mark.django_db
class TestCreditAndDiscountControls:
    @pytest.fixture
    def order(self, company, branch, item):
        customer = Customer.objects.create(
            company=company, name="Limited Client", credit_limit=Decimal("1000")
        )
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-CR-1",
            transaction_date=date.today(), branch=branch, status="Draft",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=5, rate=100)
        so.recalculate_totals()
        so.refresh_from_db()
        return so

    def test_sal_ctrl_001_within_credit_limit_passes(self, order):
        order.check_credit_limit()  # 500 <= 1000

    def test_sal_ctrl_001_over_credit_limit_blocks(self, order, item):
        SalesOrderItem.objects.create(sales_order=order, item=item, qty=20, rate=100)
        order.recalculate_totals()
        order.refresh_from_db()
        with pytest.raises(ValidationError, match="Credit limit exceeded"):
            order.check_credit_limit()

    def test_sal_ctrl_001_zero_limit_means_unconfigured_not_zero(self, company, branch, item):
        customer = Customer.objects.create(company=company, name="No Limit", credit_limit=0)
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-CR-2",
            transaction_date=date.today(), branch=branch, status="Draft",
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=100, rate=100)
        so.recalculate_totals()
        so.refresh_from_db()
        so.check_credit_limit()  # must not raise

    def test_sal_ctrl_001_counts_other_open_orders(self, order, item, company, branch):
        order.status = "Submitted"
        order.save()
        second = SalesOrder.objects.create(
            company=company, customer=order.customer, so_number="SO-CR-3",
            transaction_date=date.today(), branch=branch, status="Draft",
        )
        SalesOrderItem.objects.create(sales_order=second, item=item, qty=8, rate=100)
        second.recalculate_totals()
        second.refresh_from_db()
        # 500 already committed + 800 new = 1300 > 1000
        with pytest.raises(ValidationError, match="Credit limit exceeded"):
            second.check_credit_limit()

    def test_sal_ctrl_004_discount_over_10pct_needs_approval(self, order):
        order.discount = Decimal("100")  # 20% of 500
        order.save()
        assert order.discount_percent == Decimal("20.00")
        with pytest.raises(ValidationError, match="requires manager approval"):
            order.check_discount_authorization()

    def test_sal_ctrl_004_discount_under_10pct_is_fine(self, order):
        order.discount = Decimal("25")  # 5%
        order.save()
        order.check_discount_authorization()

    def test_sal_ctrl_004_approved_discount_passes(self, order, company):
        from apps.hr.models import Department, Employee

        dept = Department.objects.create(company=company, name="Sales")
        manager = Employee.objects.create(
            company=company, department=dept, employee_id="E-1",
            first_name="Sales", last_name="Manager", date_of_joining=date.today(),
        )
        order.discount = Decimal("100")
        order.discount_approved_by = manager
        order.save()
        order.check_discount_authorization()

    def test_sal_ctrl_001_blocks_submission_through_the_api(self, auth_client, order, item):
        SalesOrderItem.objects.create(sales_order=order, item=item, qty=20, rate=100)
        order.recalculate_totals()
        response = auth_client.patch(
            f"/api/selling/sales-orders/{order.pk}/", {"status": "Submitted"}, format="json"
        )
        assert response.status_code == 400
        order.refresh_from_db()
        assert order.status == "Draft"
