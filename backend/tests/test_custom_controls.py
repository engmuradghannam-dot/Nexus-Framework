"""Custom controls: build a whole control (a section, or a repeating table of
rows) with grouped fields and links — no code.

A control groups fields; a table control adds rows, each carrying the control's
fields, with formula fields computed per row — a mini spreadsheet inside any
module's form.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.customfields.models import (
    CustomControl, CustomControlRow, CustomField, CustomFieldValue,
)


@pytest.fixture
def auth_client(db, django_user_model):
    u = django_user_model.objects.create_superuser(email="cc@x.com", password="x")
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.mark.django_db
class TestDefiningControls:
    def test_create_a_table_control_with_fields(self, auth_client):
        r = auth_client.post("/api/customfields/controls/", {
            "module": "invoicing", "control_key": "extra_lines",
            "label": "Extra Lines", "layout": "table",
        }, format="json")
        assert r.status_code == 201, r.data
        cid = r.data["id"]
        for f in [
            {"field_key": "qty", "label": "Qty", "field_type": "number"},
            {"field_key": "price", "label": "Price", "field_type": "number"},
            {"field_key": "line_total", "label": "Total", "field_type": "formula",
             "formula": "{qty} * {price}"},
        ]:
            r = auth_client.post("/api/customfields/fields/",
                                 {"module": "invoicing", "control": cid, **f}, format="json")
            assert r.status_code == 201, r.data
        # The control now reports its nested fields.
        r = auth_client.get(f"/api/customfields/controls/{cid}/")
        assert len(r.data["fields"]) == 3

    def test_link_requires_table_layout(self, auth_client):
        r = auth_client.post("/api/customfields/controls/", {
            "module": "invoicing", "control_key": "bad", "label": "x",
            "layout": "section", "linked_module": "selling",
            "linked_match_local": "a", "linked_match_source": "b",
        }, format="json")
        assert r.status_code == 400

    def test_link_requires_its_match_fields(self, auth_client):
        r = auth_client.post("/api/customfields/controls/", {
            "module": "invoicing", "control_key": "l", "label": "x",
            "layout": "table", "linked_module": "selling",
        }, format="json")
        assert r.status_code == 400


@pytest.mark.django_db
class TestControlRows:
    def _table(self):
        ctrl = CustomControl.objects.create(
            module="invoicing", control_key="lines", label="Lines", layout="table"
        )
        CustomField.objects.create(module="invoicing", control=ctrl, field_key="desc",
                                   label="Desc", field_type="text")
        CustomField.objects.create(module="invoicing", control=ctrl, field_key="qty",
                                   label="Qty", field_type="number")
        CustomField.objects.create(module="invoicing", control=ctrl, field_key="price",
                                   label="Price", field_type="number")
        CustomField.objects.create(module="invoicing", control=ctrl, field_key="total",
                                   label="Total", field_type="formula", formula="{qty} * {price}")
        return ctrl

    def test_store_rows_and_compute_per_row(self, auth_client):
        ctrl = self._table()
        r = auth_client.post(f"/api/customfields/controls/{ctrl.id}/records/501/", {
            "rows": [
                {"desc": "A", "qty": "2", "price": "100"},
                {"desc": "B", "qty": "3", "price": "50"},
            ],
        }, format="json")
        assert r.status_code == 200
        rows = r.data["rows"]
        assert len(rows) == 2
        assert Decimal(rows[0]["total"]) == Decimal("200")
        assert Decimal(rows[1]["total"]) == Decimal("150")

    def test_rows_persist_and_reread(self, auth_client):
        ctrl = self._table()
        auth_client.post(f"/api/customfields/controls/{ctrl.id}/records/7/", {
            "rows": [{"desc": "X", "qty": "1", "price": "9"}],
        }, format="json")
        r = auth_client.get(f"/api/customfields/controls/{ctrl.id}/records/7/")
        assert len(r.data["rows"]) == 1
        assert r.data["rows"][0]["desc"] == "X"

    def test_posting_rows_replaces_the_previous_set(self, auth_client):
        ctrl = self._table()
        url = f"/api/customfields/controls/{ctrl.id}/records/9/"
        auth_client.post(url, {"rows": [{"desc": "old", "qty": "1", "price": "1"}]}, format="json")
        auth_client.post(url, {"rows": [{"desc": "new", "qty": "2", "price": "2"}]}, format="json")
        r = auth_client.get(url)
        assert len(r.data["rows"]) == 1
        assert r.data["rows"][0]["desc"] == "new"
        # No orphaned rows or values left behind.
        assert CustomControlRow.objects.filter(control=ctrl, record_id="9").count() == 1

    def test_computed_field_not_stored_in_rows(self, auth_client):
        ctrl = self._table()
        auth_client.post(f"/api/customfields/controls/{ctrl.id}/records/11/", {
            "rows": [{"desc": "A", "qty": "2", "price": "100", "total": "9999"}],
        }, format="json")
        assert not CustomFieldValue.objects.filter(
            field__field_key="total", record_id="11"
        ).exists()

    def test_rows_refused_on_a_section_control(self, auth_client):
        ctrl = CustomControl.objects.create(
            module="invoicing", control_key="sec", label="Sec", layout="section"
        )
        r = auth_client.post(f"/api/customfields/controls/{ctrl.id}/records/1/", {
            "rows": [{"x": "1"}],
        }, format="json")
        assert r.status_code == 400
