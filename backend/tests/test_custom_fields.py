"""Custom fields: define fields for any module without code, with Excel-like
formula and lookup fields.

The formula evaluator must be a calculator, never an interpreter — user-supplied
expressions run through an ast walker that permits only arithmetic, so a field
definition can never become a code-execution vector. Computed fields are derived
on read and never stored, so they can't drift from their inputs.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.customfields.engine import FormulaError, evaluate_formula
from apps.customfields.models import CustomField, CustomFieldValue
from apps.inventory.models import Item


@pytest.fixture
def auth_client(db, django_user_model):
    u = django_user_model.objects.create_superuser(email="cf@x.com", password="x")
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="CF Co", code="CF-CO")


@pytest.mark.django_db
class TestFormulaEngineSafety:
    """The security boundary: arithmetic in, never code."""

    @pytest.mark.parametrize("expr", [
        "__import__('os').system('ls')",
        "{x}.__class__.__bases__",
        "eval('2+2')",
        "open('/etc/passwd').read()",
        "abs({x})",
        "{x} ** 999",
        "[i for i in range(9)]",
    ])
    def test_dangerous_expressions_are_refused(self, expr):
        with pytest.raises(FormulaError):
            evaluate_formula(expr, {"x": 1})

    def test_arithmetic_is_correct(self):
        assert evaluate_formula("{a} + {b} * 2", {"a": 5, "b": 4}) == Decimal(13)
        assert evaluate_formula("({a} + {b}) * 2", {"a": 5, "b": 4}) == Decimal(18)
        assert evaluate_formula("{p} * 1.15", {"p": 100}) == Decimal("115.00")

    def test_division_by_zero_is_refused(self):
        with pytest.raises(FormulaError):
            evaluate_formula("{a} / 0", {"a": 5})

    def test_unknown_reference_is_refused(self):
        with pytest.raises(FormulaError):
            evaluate_formula("{missing} + 1", {"a": 1})


@pytest.mark.django_db
class TestDefiningFields:
    def test_define_plain_and_formula_fields(self, auth_client):
        for payload in [
            {"module": "inventory", "field_key": "qty", "label": "Qty", "field_type": "number"},
            {"module": "inventory", "field_key": "price", "label": "Price", "field_type": "number"},
            {"module": "inventory", "field_key": "total", "label": "Total",
             "field_type": "formula", "formula": "{qty} * {price} * 1.15"},
        ]:
            r = auth_client.post("/api/customfields/fields/", payload, format="json")
            assert r.status_code == 201, r.data

    def test_unsafe_formula_is_rejected_at_definition(self, auth_client):
        r = auth_client.post("/api/customfields/fields/", {
            "module": "inventory", "field_key": "bad", "label": "x",
            "field_type": "formula", "formula": "__import__('os').system('x')",
        }, format="json")
        assert r.status_code == 400

    def test_formula_field_requires_a_formula(self, auth_client):
        r = auth_client.post("/api/customfields/fields/", {
            "module": "inventory", "field_key": "f", "label": "x", "field_type": "formula",
        }, format="json")
        assert r.status_code == 400

    def test_lookup_field_requires_its_config(self, auth_client):
        r = auth_client.post("/api/customfields/fields/", {
            "module": "inventory", "field_key": "l", "label": "x", "field_type": "lookup",
        }, format="json")
        assert r.status_code == 400


@pytest.mark.django_db
class TestRecordValues:
    def _define(self, company):
        CustomField.objects.create(module="inventory", field_key="qty", label="Qty", field_type="number")
        CustomField.objects.create(module="inventory", field_key="price", label="Price", field_type="number")
        CustomField.objects.create(
            module="inventory", field_key="total", label="Total",
            field_type="formula", formula="{qty} * {price} * 1.15",
        )
        return Item.objects.create(company=company, item_code="I-1", item_name="x")

    def test_store_inputs_and_read_computed(self, auth_client, company):
        item = self._define(company)
        r = auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"qty": "5", "price": "200"}, format="json",
        )
        assert r.status_code == 200
        values = {f["field_key"]: f["value"] for f in r.data["fields"]}
        assert Decimal(values["total"]) == Decimal("1150.00")

    def test_formula_follows_its_inputs(self, auth_client, company):
        item = self._define(company)
        auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"qty": "5", "price": "200"}, format="json",
        )
        r = auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"qty": "10", "price": "200"}, format="json",
        )
        values = {f["field_key"]: f["value"] for f in r.data["fields"]}
        assert Decimal(values["total"]) == Decimal("2300.00")

    def test_computed_value_is_never_stored(self, auth_client, company):
        item = self._define(company)
        auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"qty": "5", "price": "200", "total": "999"}, format="json",
        )
        # 'total' must not have been persisted as an input.
        assert not CustomFieldValue.objects.filter(
            field__field_key="total", record_id=str(item.pk)
        ).exists()

    def test_cannot_post_a_value_for_a_computed_field(self, auth_client, company):
        self._define(company)
        total = CustomField.objects.get(field_key="total")
        item = Item.objects.create(company=company, item_code="I-2", item_name="y")
        r = auth_client.post("/api/customfields/values/", {
            "field": total.id, "record_id": str(item.pk), "value": "5",
        }, format="json")
        assert r.status_code == 400


@pytest.mark.django_db
class TestLookup:
    def test_lookup_pulls_from_another_module(self, auth_client, company):
        """A lookup on the item's own code returns a real model field."""
        item = Item.objects.create(
            company=company, item_code="SKU-9", item_name="Widget", standard_rate=Decimal("50")
        )
        CustomField.objects.create(module="inventory", field_key="sku", label="SKU", field_type="text")
        CustomField.objects.create(
            module="inventory", field_key="catalog_name", label="Name",
            field_type="lookup", lookup_module="inventory",
            lookup_match_local="sku", lookup_match_source="item_code",
            lookup_return="item_name",
        )
        auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"sku": "SKU-9"}, format="json",
        )
        r = auth_client.get(f"/api/customfields/fields/records/inventory/{item.pk}/")
        values = {f["field_key"]: f["value"] for f in r.data["fields"]}
        assert values["catalog_name"] == "Widget"

    def test_lookup_with_no_match_is_blank_not_error(self, auth_client, company):
        item = Item.objects.create(company=company, item_code="REAL", item_name="x")
        CustomField.objects.create(module="inventory", field_key="sku", label="SKU", field_type="text")
        CustomField.objects.create(
            module="inventory", field_key="found", label="Found",
            field_type="lookup", lookup_module="inventory",
            lookup_match_local="sku", lookup_match_source="item_code",
            lookup_return="item_name",
        )
        auth_client.post(
            f"/api/customfields/fields/records/inventory/{item.pk}/",
            {"sku": "DOES-NOT-EXIST"}, format="json",
        )
        r = auth_client.get(f"/api/customfields/fields/records/inventory/{item.pk}/")
        values = {f["field_key"]: f["value"] for f in r.data["fields"]}
        assert values["found"] is None
