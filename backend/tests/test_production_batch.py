"""Batch manufacturing with formulation (potency) and genealogy.

A production batch records the finished lot of a work order and every input
batch consumed to make it. Where a BOM line is potency-managed, the physical
quantity drawn scales by the input batch's assay — a 95%-potency batch supplies
less active per unit, so more is consumed. The genealogy supports recalls in
both directions.
"""
from decimal import Decimal

import pytest

from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item, ItemBatch
from apps.manufacturing.models import BOM, BOMItem, ProductionBatch, WorkOrder


@pytest.fixture
def setup(db):
    c = CompanyProfile.objects.create(name="Pharma", code="PH")
    b = Branch.objects.create(company=c, name="b", code="PHB", address="x")
    w = Warehouse.objects.get(branch=b)
    prod = Item.objects.create(company=c, item_code="DRUG", item_name="Tablet")
    api = Item.objects.create(company=c, item_code="API", item_name="Active")
    exc = Item.objects.create(company=c, item_code="EXC", item_name="Filler")
    ItemBatch.objects.create(item=api, batch_no="API-01", quantity=1000, warehouse=w, potency=Decimal("95"))
    ItemBatch.objects.create(item=exc, batch_no="EXC-01", quantity=1000, warehouse=w, potency=Decimal("100"))
    bom = BOM.objects.create(company=c, item=prod, quantity=1000, bom_name="Tablet")
    bi_api = BOMItem.objects.create(bom=bom, item=api, qty=100, is_potency_managed=True)
    bi_exc = BOMItem.objects.create(bom=bom, item=exc, qty=50, is_potency_managed=False)
    wo = WorkOrder.objects.create(company=c, branch=b, bom=bom, wo_number="WO-B1",
                                  item_to_manufacture=prod, qty_to_produce=1000, warehouse=w)
    return dict(c=c, w=w, prod=prod, api=api, exc=exc, bom=bom, bi_api=bi_api, bi_exc=bi_exc, wo=wo)


@pytest.mark.django_db
class TestPotencyAdjustment:
    def test_potency_managed_line_scales_up(self, setup):
        # 100 nominal at 95% potency -> 100 * 100/95.
        assert setup["bi_api"].potency_adjusted_qty(Decimal("95")) == Decimal("105.2632")

    def test_unmanaged_line_is_unchanged(self, setup):
        assert setup["bi_exc"].potency_adjusted_qty(Decimal("100")) == Decimal("50")

    def test_full_potency_managed_line_is_nominal(self, setup):
        assert setup["bi_api"].potency_adjusted_qty(Decimal("100")) == Decimal("100.0000")


@pytest.mark.django_db
class TestBatchProduction:
    def _produce(self, s):
        return s["wo"].produce_batch("DRUG-LOT-001", {
            s["bi_api"].id: ("API-01", Decimal("95")),
            s["bi_exc"].id: ("EXC-01", Decimal("100")),
        })

    def test_records_all_consumptions(self, setup):
        pb = self._produce(setup)
        assert pb.consumptions.count() == 2

    def test_consumption_stores_nominal_and_actual(self, setup):
        pb = self._produce(setup)
        api_row = pb.consumptions.get(input_batch_no="API-01")
        assert api_row.nominal_qty == Decimal("100.0000")
        assert api_row.actual_qty == Decimal("105.2632")

    def test_draws_down_the_input_batch(self, setup):
        self._produce(setup)
        api_batch = ItemBatch.objects.get(item=setup["api"], batch_no="API-01")
        # 1000 - 105.2632, quantised to the field's 2 decimals.
        assert api_batch.quantity == Decimal("894.74")

    def test_creates_the_output_batch_in_stock(self, setup):
        self._produce(setup)
        out = ItemBatch.objects.get(item=setup["prod"], batch_no="DRUG-LOT-001")
        assert out.quantity == Decimal("1000.00")

    def test_insufficient_batch_is_refused(self, setup):
        from django.core.exceptions import ValidationError
        # Drain the API batch first.
        b = ItemBatch.objects.get(item=setup["api"], batch_no="API-01")
        b.quantity = Decimal("10")
        b.save()
        with pytest.raises(ValidationError):
            self._produce(setup)

    def test_missing_input_batch_is_refused(self, setup):
        from django.core.exceptions import ValidationError
        with pytest.raises(ValidationError):
            setup["wo"].produce_batch("LOT-X", {
                setup["bi_api"].id: ("API-01", Decimal("95")),
                # EXC missing
            })


@pytest.mark.django_db
class TestGenealogy:
    def test_backward_trace_lists_inputs(self, setup):
        pb = setup["wo"].produce_batch("DRUG-LOT-001", {
            setup["bi_api"].id: ("API-01", Decimal("95")),
            setup["bi_exc"].id: ("EXC-01", Decimal("100")),
        })
        inputs = {c.input_batch_no for c in pb.trace_inputs()}
        assert inputs == {"API-01", "EXC-01"}

    def test_forward_trace_finds_batches_using_an_input(self, setup):
        setup["wo"].produce_batch("DRUG-LOT-001", {
            setup["bi_api"].id: ("API-01", Decimal("95")),
            setup["bi_exc"].id: ("EXC-01", Decimal("100")),
        })
        # Which finished batches contain input API-01? (recall direction)
        hits = ProductionBatch.objects.filter(consumptions__input_batch_no="API-01").distinct()
        assert hits.count() == 1
        assert hits.first().output_batch_no == "DRUG-LOT-001"


@pytest.mark.django_db
class TestBatchAPI:
    def test_produce_batch_endpoint(self, setup, django_user_model):
        from rest_framework.test import APIClient
        admin = django_user_model.objects.create_superuser(email="a@x.com", password="x")
        client = APIClient()
        client.force_authenticate(admin)
        r = client.post(f"/api/manufacturing/work-orders/{setup['wo'].id}/produce_batch/", {
            "output_batch_no": "DRUG-LOT-API",
            "inputs": {
                str(setup["bi_api"].id): {"batch_no": "API-01", "potency": "95"},
                str(setup["bi_exc"].id): {"batch_no": "EXC-01", "potency": "100"},
            },
        }, format="json")
        assert r.status_code == 201, r.data
        assert len(r.data["consumptions"]) == 2
