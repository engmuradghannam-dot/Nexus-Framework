"""Tests for the auto-reorder feature (apps.records.ModuleRecordViewSet.low_stock
/ create_purchase_orders).

Previously low_stock() read from ModuleRecord, a generic freeform-JSON
store completely disconnected from apps.inventory.Item -- so it never
reflected real stock movements from Buying/Selling/Manufacturing. Fixed to
query real Item/StockEntry data, and added create_purchase_orders to
actually deliver "auto" reorder (grouped draft POs per supplier) rather
than just a read-only alert list.
"""
import pytest
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, StockEntry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="reorder@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Reorder Co", code="REORD-CO")


@pytest.fixture
def warehouse(company):
    branch = Branch.objects.create(company=company, name="Main Branch", code="REORD-MB", address="Riyadh")
    return Warehouse.objects.create(branch=branch, name="Main WH", code="REORD-WH")


@pytest.fixture
def supplier(company):
    return Supplier.objects.create(company=company, name="Reorder Supplier")


@pytest.mark.django_db
class TestLowStockAlerts:
    def test_item_below_reorder_level_is_flagged(self, auth_client, company, supplier, warehouse):
        item = Item.objects.create(
            company=company, item_code="LOW-1", item_name="Low Stock Item",
            reorder_level=10, reorder_qty=50, supplier=supplier, standard_rate=5,
        )
        StockEntry.objects.create(company=company, warehouse=warehouse, item=item, entry_type="Receipt", quantity=3, rate=5)

        response = auth_client.get("/api/records/low_stock/", {"company": str(company.id)})
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["alerts"][0]["item_code"] == "LOW-1"
        assert response.data["alerts"][0]["suggested_order_qty"] == 50

    def test_item_above_reorder_level_not_flagged(self, auth_client, company, supplier, warehouse):
        item = Item.objects.create(
            company=company, item_code="OK-1", item_name="Healthy Stock Item",
            reorder_level=10, supplier=supplier,
        )
        StockEntry.objects.create(company=company, warehouse=warehouse, item=item, entry_type="Receipt", quantity=100, rate=5)

        response = auth_client.get("/api/records/low_stock/", {"company": str(company.id)})
        assert response.data["count"] == 0

    def test_item_with_no_reorder_level_ignored(self, auth_client, company):
        Item.objects.create(company=company, item_code="NRL-1", item_name="No Reorder Level")
        response = auth_client.get("/api/records/low_stock/", {"company": str(company.id)})
        assert response.data["count"] == 0


@pytest.mark.django_db
class TestAutoCreatePurchaseOrders:
    def test_creates_one_po_per_supplier_grouping_items(self, auth_client, company, supplier, warehouse):
        item1 = Item.objects.create(
            company=company, item_code="AUTO-1", item_name="A1", reorder_level=10,
            reorder_qty=20, supplier=supplier, standard_rate=5,
        )
        item2 = Item.objects.create(
            company=company, item_code="AUTO-2", item_name="A2", reorder_level=5,
            reorder_qty=15, supplier=supplier, standard_rate=3,
        )
        StockEntry.objects.create(company=company, warehouse=warehouse, item=item1, entry_type="Receipt", quantity=2, rate=5)
        StockEntry.objects.create(company=company, warehouse=warehouse, item=item2, entry_type="Receipt", quantity=1, rate=3)

        response = auth_client.post("/api/records/create_purchase_orders/", {}, format="json")
        assert response.status_code == 200
        assert len(response.data["created"]) == 1
        po = PurchaseOrder.objects.get(po_number=response.data["created"][0])
        assert po.supplier == supplier
        assert po.items.count() == 2

    def test_items_without_supplier_are_skipped_and_reported(self, auth_client, company):
        Item.objects.create(company=company, item_code="NOSUP-1", item_name="No Supplier", reorder_level=10)
        response = auth_client.post("/api/records/create_purchase_orders/", {}, format="json")
        assert response.data["created"] == []
        assert "NOSUP-1" in response.data["skipped_no_supplier"]


@pytest.mark.django_db
class TestReorderCompanyScoping:
    """low_stock/create_purchase_orders reach into apps.inventory.Item directly,
    bypassing the ViewSet's own tenant-scoped queryset. They must still scope to
    the caller's companies — otherwise any authenticated user reads, and writes
    POs against, every company in the installation."""

    @pytest.fixture
    def other_company(self):
        return CompanyProfile.objects.create(name="Rival Co", code="RIVAL-CO")

    @pytest.fixture
    def scoped_client(self, api_client, django_user_model, company):
        user = django_user_model.objects.create_user(
            email="scoped@nexus.com", password="testpass123"
        )
        user.managed_companies.add(company)
        api_client.force_authenticate(user=user)
        return api_client

    def test_low_stock_hides_other_companies_items(self, scoped_client, company, other_company):
        Item.objects.create(company=company, item_code="MINE-1", item_name="Mine", reorder_level=10)
        Item.objects.create(company=other_company, item_code="THEIRS-1", item_name="Theirs", reorder_level=10)
        response = scoped_client.get("/api/records/low_stock/")
        codes = {a["item_code"] for a in response.data["alerts"]}
        assert codes == {"MINE-1"}

    def test_create_purchase_orders_cannot_touch_other_companies(
        self, scoped_client, company, other_company
    ):
        rival_supplier = Supplier.objects.create(company=other_company, name="Rival Vendor")
        Item.objects.create(
            company=other_company, item_code="THEIRS-2", item_name="Theirs",
            reorder_level=10, reorder_qty=5, supplier=rival_supplier, standard_rate=1,
        )
        response = scoped_client.post("/api/records/create_purchase_orders/", {}, format="json")
        assert response.data["created"] == []
        assert not PurchaseOrder.objects.filter(company=other_company).exists()

    def test_anonymous_user_gets_nothing(self, api_client, company):
        Item.objects.create(company=company, item_code="MINE-2", item_name="Mine", reorder_level=10)
        response = api_client.get("/api/records/low_stock/")
        assert response.status_code in (200, 401, 403)
        if response.status_code == 200:
            assert response.data["alerts"] == []
