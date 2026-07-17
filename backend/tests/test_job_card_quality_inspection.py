"""Tests for apps.manufacturing.JobCard and QualityInspection -- both
previously entirely absent from the codebase (0 fields), despite being
core shop-floor tracking (بطاقة العمل) and QC (فحص الجودة) controls.

Also covers the removal of WorkOrderViewSet's old custom start/complete/
cancel actions, which referenced a non-existent Item.stock_qty field and
would have raised AttributeError in production; the correct path is (and
was already) the PATCH status-transition flow tested in test_manufacturing.py.
"""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import CompanyProfile
from apps.hr.models import Employee
from apps.inventory.models import Item
from apps.manufacturing.models import (
    BOM,
    JobCard,
    QualityInspection,
    QualityInspectionParameter,
    WorkOrder,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="qc@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="QC Co", code="QC-CO")


@pytest.fixture
def item(company):
    return Item.objects.create(company=company, item_code="QC-ITEM", item_name="Widget")


@pytest.fixture
def employee(company):
    return Employee.objects.create(company=company, employee_id="EMP-QC-1", first_name="Yara", last_name="K")


@pytest.fixture
def work_order(company, item):
    return WorkOrder.objects.create(
        company=company, wo_number="WO-QC-1", item_to_manufacture=item, qty_to_produce=10,
    )


@pytest.mark.django_db
class TestJobCard:
    def test_start_then_complete_tracks_time_and_cost(self, work_order, employee):
        jc = JobCard.objects.create(
            company=work_order.company, work_order=work_order, operation="Assembly",
            employee=employee, for_quantity=10, hour_rate=100,
        )
        ok, msg = jc.start()
        assert ok and jc.status == "Work In Progress"
        assert jc.started_time is not None

        jc.ended_time = jc.started_time  # deterministic: force a 0-min duration for cost check
        ok, msg = jc.complete(completed_qty=10)
        assert ok, msg
        jc.refresh_from_db()
        assert jc.status == "Completed"
        assert jc.completed_qty == 10

    def test_cannot_complete_more_than_planned_quantity(self, work_order, employee):
        jc = JobCard.objects.create(
            company=work_order.company, work_order=work_order, operation="Assembly",
            employee=employee, for_quantity=5,
        )
        jc.start()
        ok, msg = jc.complete(completed_qty=99)
        assert not ok and "تتجاوز" in msg

    def test_cannot_start_twice(self, work_order):
        jc = JobCard.objects.create(company=work_order.company, work_order=work_order, operation="Cut", for_quantity=1)
        jc.start()
        ok, msg = jc.start()
        assert not ok

    def test_api_start_and_complete_actions(self, auth_client, work_order, employee):
        jc = JobCard.objects.create(
            company=work_order.company, work_order=work_order, operation="Paint",
            employee=employee, for_quantity=3,
        )
        r1 = auth_client.post(f"/api/manufacturing/job-cards/{jc.pk}/start/")
        assert r1.status_code == 200 and r1.data["success"] is True
        r2 = auth_client.post(f"/api/manufacturing/job-cards/{jc.pk}/complete/", {"completed_qty": 3})
        assert r2.status_code == 200 and r2.data["success"] is True


@pytest.mark.django_db
class TestQualityInspection:
    def test_stays_pending_with_no_parameters(self, company, item, employee):
        qi = QualityInspection.objects.create(
            company=company, item=item, inspection_type="Incoming",
            inspected_by=employee, inspection_date=date(2026, 1, 1),
        )
        assert qi.status == "Pending"

    def test_accepted_when_all_parameters_within_range(self, company, item):
        qi = QualityInspection.objects.create(
            company=company, item=item, inspection_type="Final", inspection_date=date(2026, 1, 1),
        )
        QualityInspectionParameter.objects.create(
            inspection=qi, parameter="Length", min_value=10, max_value=20, reading_value=15,
        )
        qi.refresh_from_db()
        assert qi.status == "Accepted"

    def test_rejected_when_any_parameter_out_of_range(self, company, item):
        qi = QualityInspection.objects.create(
            company=company, item=item, inspection_type="Final", inspection_date=date(2026, 1, 1),
        )
        QualityInspectionParameter.objects.create(
            inspection=qi, parameter="Length", min_value=10, max_value=20, reading_value=15,
        )
        QualityInspectionParameter.objects.create(
            inspection=qi, parameter="Weight", min_value=1, max_value=2, reading_value=5,
        )
        qi.refresh_from_db()
        assert qi.status == "Rejected"

    def test_locked_from_edits_once_accepted(self, auth_client, company, item):
        qi = QualityInspection.objects.create(
            company=company, item=item, inspection_type="Final", inspection_date=date(2026, 1, 1),
        )
        QualityInspectionParameter.objects.create(
            inspection=qi, parameter="Length", min_value=10, max_value=20, reading_value=15,
        )
        response = auth_client.patch(
            f"/api/manufacturing/quality-inspections/{qi.pk}/", {"remarks": "changed after the fact"}
        )
        assert response.status_code == 403

    def test_reference_work_order_link(self, company, item, work_order):
        qi = QualityInspection.objects.create(
            company=company, item=item, inspection_type="In Process",
            reference_work_order=work_order, inspection_date=date(2026, 1, 1),
        )
        assert qi.reference_work_order == work_order
        assert work_order.quality_inspections.count() == 1
