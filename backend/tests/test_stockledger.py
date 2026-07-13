"""Pytest tests for the Stock Ledger module (apps.stockledger).

Covers the FIFO/LIFO/Moving-Average valuation engine and the stock
movement API (transfer, valuation) — inventory valuation directly affects
the balance sheet, and had no test coverage (P1 #4 follow-up).
"""
from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.stockledger.models import StockMovement, valuate


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="warehouse@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


class TestValuate:
    """Pure-function tests against the textbook example:
    receive 10 @ 10, receive 10 @ 12, issue 15.
    """

    def _movements(self):
        return [
            {"movement_type": "in", "quantity": 10, "unit_cost": 10},
            {"movement_type": "in", "quantity": 10, "unit_cost": 12},
            {"movement_type": "out", "quantity": 15, "unit_cost": 0},
        ]

    def test_closing_quantity(self):
        result = valuate(self._movements())
        assert result["closing_qty"] == 5

    def test_fifo_value_uses_most_recent_lot(self):
        # FIFO consumes the 10@10 lot first, then 5 from the 10@12 lot,
        # leaving 5 units from the 12-cost lot.
        result = valuate(self._movements())
        assert result["fifo_value"] == 60.0

    def test_lifo_value_uses_oldest_lot(self):
        # LIFO consumes the 10@12 lot first, then 5 from the 10@10 lot,
        # leaving 5 units from the 10-cost lot.
        result = valuate(self._movements())
        assert result["lifo_value"] == 50.0

    def test_moving_average_value(self):
        # Average cost before the issue: (10*10 + 10*12) / 20 = 11.
        # Remaining 5 units valued at that average = 55.
        result = valuate(self._movements())
        assert result["moving_avg_cost"] == 11.0
        assert result["moving_avg_value"] == 55.0

    def test_issuing_more_than_on_hand_does_not_go_negative(self):
        movements = [
            {"movement_type": "in", "quantity": 5, "unit_cost": 10},
            {"movement_type": "out", "quantity": 20, "unit_cost": 0},
        ]
        result = valuate(movements)
        assert result["closing_qty"] == 0
        assert result["fifo_value"] == 0
        assert result["moving_avg_value"] == 0

    def test_no_movements_returns_zeroed_result(self):
        result = valuate([])
        assert result["closing_qty"] == 0
        assert result["fifo_value"] == 0
        assert result["lifo_value"] == 0
        assert result["moving_avg_value"] == 0


@pytest.mark.django_db
class TestStockMovementAPI:
    def test_transfer_creates_out_and_in_movements(self, auth_client):
        response = auth_client.post(
            "/api/stock/movements/transfer/",
            {
                "item_code": "SKU-1",
                "item_name": "Widget",
                "from_warehouse": "WH-A",
                "to_warehouse": "WH-B",
                "quantity": 10,
                "unit_cost": 5,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert StockMovement.objects.filter(item_code="SKU-1", movement_type="out", warehouse="WH-A").exists()
        assert StockMovement.objects.filter(item_code="SKU-1", movement_type="in", warehouse="WH-B").exists()

    def test_transfer_rejects_same_source_and_destination(self, auth_client):
        response = auth_client.post(
            "/api/stock/movements/transfer/",
            {"item_code": "SKU-1", "from_warehouse": "WH-A", "to_warehouse": "WH-A", "quantity": 5},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_transfer_rejects_zero_quantity(self, auth_client):
        response = auth_client.post(
            "/api/stock/movements/transfer/",
            {"item_code": "SKU-1", "from_warehouse": "WH-A", "to_warehouse": "WH-B", "quantity": 0},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valuation_endpoint_aggregates_per_item(self, auth_client):
        StockMovement.objects.create(
            item_code="SKU-2", item_name="Gadget", warehouse="WH-A",
            movement_type="in", quantity=10, unit_cost=20, date=date(2026, 1, 1),
        )
        StockMovement.objects.create(
            item_code="SKU-2", item_name="Gadget", warehouse="WH-A",
            movement_type="out", quantity=4, unit_cost=0, date=date(2026, 1, 5),
        )
        response = auth_client.get("/api/stock/movements/valuation/")
        assert response.status_code == status.HTTP_200_OK
        row = next(r for r in response.data["rows"] if r["item_code"] == "SKU-2")
        assert row["closing_qty"] == 6
        assert row["fifo_value"] == 120.0

    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get("/api/stock/movements/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
