"""Finite-capacity scheduling — booking work orders on workstations.

A workstation does one job at a time, so slots on the same station may not
overlap. The scheduler can also find the earliest free window of a given length,
which is what turns a due-date plan into a shop-floor timeline.
"""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.models import Branch, CompanyProfile
from apps.inventory.models import Item
from apps.manufacturing.models import ScheduleSlot, WorkOrder, Workstation


@pytest.fixture
def setup(db):
    c = CompanyProfile.objects.create(name="Factory", code="FC")
    b = Branch.objects.create(company=c, name="b", code="FCB", address="x")
    prod = Item.objects.create(company=c, item_code="P", item_name="Product")
    ws = Workstation.objects.create(company=c, name="CNC-1", code="CNC1")
    t0 = timezone.now().replace(hour=8, minute=0, second=0, microsecond=0)
    n = {"i": 0}

    def wo():
        n["i"] += 1
        return WorkOrder.objects.create(company=c, branch=b, wo_number=f"WO-{n['i']}",
                                        item_to_manufacture=prod, qty_to_produce=10)
    return dict(c=c, ws=ws, t0=t0, wo=wo)


@pytest.mark.django_db
class TestFiniteCapacity:
    def test_book_a_slot(self, setup):
        s = ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        assert s.pk is not None

    def test_overlapping_slot_is_refused(self, setup):
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        with pytest.raises(ValidationError):
            ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
                work_order=setup["wo"](), start=setup["t0"] + timedelta(hours=1),
                end=setup["t0"] + timedelta(hours=3))

    def test_adjacent_slot_is_allowed(self, setup):
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        s2 = ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"] + timedelta(hours=2),
            end=setup["t0"] + timedelta(hours=4))
        assert s2.pk is not None

    def test_end_before_start_is_refused(self, setup):
        with pytest.raises(ValidationError):
            ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
                work_order=setup["wo"](), start=setup["t0"],
                end=setup["t0"] - timedelta(hours=1))

    def test_other_station_is_independent(self, setup):
        ws2 = Workstation.objects.create(company=setup["c"], name="CNC-2", code="CNC2")
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        # Same window on a different station is fine.
        s = ScheduleSlot.objects.create(company=setup["c"], workstation=ws2,
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        assert s.pk is not None

    def test_cancelled_slot_frees_the_window(self, setup):
        s1 = ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        s1.status = "cancelled"
        s1.save()
        # The window is free again.
        s2 = ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        assert s2.pk is not None


@pytest.mark.django_db
class TestEarliestFreeWindow:
    def test_finds_gap_after_bookings(self, setup):
        for h in (0, 2):
            ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
                work_order=setup["wo"](), start=setup["t0"] + timedelta(hours=h),
                end=setup["t0"] + timedelta(hours=h + 2))
        # Booked 8-10 and 10-12; earliest hour-long window is 12:00.
        free = ScheduleSlot.earliest_free_window(setup["ws"], timedelta(hours=1), setup["t0"])
        assert free == setup["t0"] + timedelta(hours=4)

    def test_fills_an_interior_gap(self, setup):
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"] + timedelta(hours=4),
            end=setup["t0"] + timedelta(hours=6))
        # Gap 10-12 fits a 1h job.
        free = ScheduleSlot.earliest_free_window(setup["ws"], timedelta(hours=1), setup["t0"])
        assert free == setup["t0"] + timedelta(hours=2)


@pytest.mark.django_db
class TestSchedulingAPI:
    def test_earliest_free_endpoint(self, setup, django_user_model):
        from rest_framework.test import APIClient
        admin = django_user_model.objects.create_superuser(email="a@x.com", password="x")
        c = APIClient()
        c.force_authenticate(admin)
        r = c.get("/api/manufacturing/schedule-slots/earliest_free/",
                  {"workstation": setup["ws"].id, "minutes": 60})
        assert r.status_code == 200
        assert "earliest_start" in r.data

    def test_api_refuses_overlap(self, setup, django_user_model):
        from rest_framework.test import APIClient
        admin = django_user_model.objects.create_superuser(email="a@x.com", password="x")
        c = APIClient()
        c.force_authenticate(admin)
        ScheduleSlot.objects.create(company=setup["c"], workstation=setup["ws"],
            work_order=setup["wo"](), start=setup["t0"], end=setup["t0"] + timedelta(hours=2))
        r = c.post("/api/manufacturing/schedule-slots/", {
            "company": setup["c"].id, "workstation": setup["ws"].id,
            "work_order": setup["wo"]().id,
            "start": (setup["t0"] + timedelta(hours=1)).isoformat(),
            "end": (setup["t0"] + timedelta(hours=3)).isoformat(),
        }, format="json")
        assert r.status_code == 400
