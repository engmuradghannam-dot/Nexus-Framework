"""CDHDR/CDPOS change documents — queryable field-level history.

Splits an audit record into a header (who/when/which object) and one item per
changed field (field, old, new), so field-level questions — 'every change to
this field', 'who set this value' — are answerable. Sensitive fields are tracked
but their values masked.
"""
import pytest

from apps.audit.changedoc import (
    _display, record_change, record_create, record_delete, snapshot,
)
from apps.audit.models import ChangeDocument, ChangeDocumentItem
from apps.core.models import CompanyProfile
from apps.inventory.models import Item


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(email="ed@x.com", password="x")


@pytest.fixture
def item(db):
    c = CompanyProfile.objects.create(name="A", code="AC")
    return Item.objects.create(company=c, item_code="I1", item_name="Steel", standard_rate=100)


@pytest.mark.django_db
class TestRecorder:
    def test_create_records_initial_values(self, item, user):
        h = record_create(item, user=user)
        assert h.operation == "create"
        assert h.items.filter(field_name="item_name", new_value="Steel").exists()

    def test_update_captures_field_diff(self, item, user):
        before = snapshot(item)
        item.item_name = "Steel Sheet"
        item.standard_rate = 150
        item.save()
        h = record_change(item, before, user=user, reason="price update")
        names = set(h.items.values_list("field_name", flat=True))
        assert names == {"item_name", "standard_rate"}
        row = h.items.get(field_name="standard_rate")
        assert row.old_value == "100" and row.new_value == "150"
        assert h.reason == "price update"

    def test_no_change_writes_nothing(self, item, user):
        before = snapshot(item)
        item.save()
        assert record_change(item, before, user=user) is None

    def test_delete_preserves_final_values(self, item, user):
        h = record_delete(item, user=user)
        assert h.operation == "delete"
        assert h.items.filter(field_name="item_name", old_value="Steel").exists()


@pytest.mark.django_db
class TestSensitiveMasking:
    def test_sensitive_values_are_masked(self):
        assert _display("salary", 50000) == "••••••"
        assert _display("iban", "SA1234") == "••••••"

    def test_ordinary_values_are_shown(self):
        assert _display("item_name", "Steel") == "Steel"


@pytest.mark.django_db
class TestFieldLevelQuery:
    def test_history_is_queryable_by_field(self, item, user):
        before = snapshot(item)
        item.standard_rate = 150
        item.save()
        record_change(item, before, user=user)
        # The whole point of CDPOS: ask for every change to one field.
        rows = ChangeDocumentItem.objects.filter(field_name="standard_rate")
        assert rows.filter(old_value="100", new_value="150").exists()


@pytest.mark.django_db
class TestChangeDocumentAPI:
    def test_trail_is_read_only(self, item, user, django_user_model):
        from rest_framework.test import APIClient
        record_create(item, user=user)
        admin = django_user_model.objects.create_superuser(email="a@x.com", password="x")
        c = APIClient()
        c.force_authenticate(admin)
        # Listing works…
        r = c.get("/api/audit/change-documents/")
        assert r.status_code == 200
        # …but writing is refused (ReadOnly viewset).
        r = c.post("/api/audit/change-documents/", {}, format="json")
        assert r.status_code == 405
