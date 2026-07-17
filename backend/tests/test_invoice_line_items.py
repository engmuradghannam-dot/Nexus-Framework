"""Tests for Invoice line items (apps.invoicing.InvoiceItem) and the
Sales/Purchase Order -> Invoice conversion.

Invoice is the ZATCA-facing e-invoicing document but carried no item-level
detail at all — just a hand-typed subtotal — and there was no way to bill a
submitted order without re-entering every line by hand.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient

from apps.buying.models import PurchaseOrder, PurchaseOrderItem, PurchaseTaxCharge, Supplier
from apps.core.models import Branch, CompanyProfile, Warehouse
from apps.inventory.models import Item
from apps.invoicing.models import Invoice, InvoiceItem
from apps.selling.models import Customer, SalesOrder, SalesOrderItem, SalesTaxCharge


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="billing@nexus.com", password="testpass123"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def company():
    return CompanyProfile.objects.create(name="Billing Co", code="BILL-CO")


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, name="HQ", code="HQ", address="Riyadh")


@pytest.fixture
def warehouse(branch):
    return Warehouse.objects.create(branch=branch, name="Main WH", code="MWH")


@pytest.fixture
def item(company):
    return Item.objects.create(
        company=company, item_code="SKU-1", item_name="Widget", standard_rate=100
    )


@pytest.fixture
def item2(company):
    return Item.objects.create(
        company=company, item_code="SKU-2", item_name="Gadget", standard_rate=200
    )


@pytest.fixture
def customer(company):
    return Customer.objects.create(company=company, name="Client A")


@pytest.fixture
def supplier(company):
    return Supplier.objects.create(company=company, name="Vendor B")


@pytest.fixture
def invoice(company):
    return Invoice.objects.create(
        company=company,
        invoice_type="sales",
        invoice_number="INV-LINES-1",
        party_name="Client A",
        invoice_date=date(2026, 1, 15),
    )


@pytest.mark.django_db
class TestInvoiceItem:
    def test_line_items_drive_invoice_totals(self, invoice, item, item2):
        InvoiceItem.objects.create(invoice=invoice, item=item, qty=2, rate=100, tax_rate=15)
        InvoiceItem.objects.create(invoice=invoice, item=item2, qty=1, rate=200, tax_rate=15)
        invoice.refresh_from_db()
        assert invoice.subtotal == Decimal("400.00")
        assert invoice.tax_amount == Decimal("60.00")
        assert invoice.total == Decimal("460.00")

    def test_line_copies_item_code_and_name(self, invoice, item):
        line = InvoiceItem.objects.create(invoice=invoice, item=item, qty=1, rate=100)
        assert line.item_code == "SKU-1"
        assert line.item_name == "Widget"

    def test_mixed_tax_rates_are_respected_per_line(self, invoice, item, item2):
        """A zero-rated export line alongside a standard 15% line — the whole
        reason per-line VAT exists for ZATCA."""
        InvoiceItem.objects.create(invoice=invoice, item=item, qty=1, rate=100, tax_rate=15)
        InvoiceItem.objects.create(invoice=invoice, item=item2, qty=1, rate=100, tax_rate=0)
        invoice.refresh_from_db()
        assert invoice.subtotal == Decimal("200.00")
        assert invoice.tax_amount == Decimal("15.00")
        assert invoice.total == Decimal("215.00")

    def test_saving_invoice_does_not_clobber_line_item_totals(self, invoice, item, item2):
        """Invoice.save() calls recompute(), which derives tax from the flat
        subtotal * tax_rate. With line items present that must not overwrite the
        per-line VAT."""
        InvoiceItem.objects.create(invoice=invoice, item=item, qty=1, rate=100, tax_rate=15)
        InvoiceItem.objects.create(invoice=invoice, item=item2, qty=1, rate=100, tax_rate=0)
        invoice.refresh_from_db()
        invoice.notes = "touched"
        invoice.save()
        invoice.refresh_from_db()
        assert invoice.tax_amount == Decimal("15.00")
        assert invoice.total == Decimal("215.00")

    def test_deleting_last_line_zeroes_totals(self, invoice, item):
        line = InvoiceItem.objects.create(invoice=invoice, item=item, qty=2, rate=100, tax_rate=15)
        invoice.refresh_from_db()
        assert invoice.total == Decimal("230.00")
        line.delete()
        invoice.refresh_from_db()
        assert invoice.subtotal == Decimal("0.00")
        assert invoice.tax_amount == Decimal("0.00")
        assert invoice.total == Decimal("0.00")

    def test_deleting_invoice_cascades_without_error(self, invoice, item):
        InvoiceItem.objects.create(invoice=invoice, item=item, qty=1, rate=100)
        invoice_id = invoice.pk
        invoice.delete()
        assert not InvoiceItem.objects.filter(invoice_id=invoice_id).exists()

    def test_flat_entry_invoice_still_works(self, company):
        """No line items: the legacy subtotal * tax_rate path still owns totals."""
        inv = Invoice.objects.create(
            company=company, invoice_type="sales", invoice_number="INV-FLAT-1",
            party_name="Client A", invoice_date=date(2026, 1, 15),
            subtotal=Decimal("1000"), tax_rate=Decimal("15"),
        )
        assert inv.tax_amount == Decimal("150.00")
        assert inv.total == Decimal("1150.00")

    def test_discount_is_subtracted_from_total(self, invoice, item):
        invoice.discount = Decimal("50")
        invoice.save()
        InvoiceItem.objects.create(invoice=invoice, item=item, qty=2, rate=100, tax_rate=15)
        invoice.refresh_from_db()
        assert invoice.subtotal == Decimal("200.00")
        assert invoice.tax_amount == Decimal("30.00")
        assert invoice.total == Decimal("180.00")


@pytest.fixture
def sales_order(company, customer, branch, warehouse, item, item2):
    so = SalesOrder.objects.create(
        company=company, customer=customer, so_number="SO-CONV-1",
        transaction_date=date(2026, 1, 10), branch=branch, warehouse=warehouse,
        status="Submitted",
    )
    SalesOrderItem.objects.create(sales_order=so, item=item, qty=2, rate=100)
    SalesOrderItem.objects.create(sales_order=so, item=item2, qty=1, rate=200)
    SalesTaxCharge.objects.create(sales_order=so, tax_rate=15, tax_amount=Decimal("60"))
    so.recalculate_totals()
    so.refresh_from_db()
    return so


@pytest.mark.django_db
class TestSalesOrderToInvoice:
    def test_conversion_copies_every_line(self, sales_order):
        inv = Invoice.create_from_sales_order(
            sales_order, invoice_number="INV-FROM-SO-1", invoice_date=date(2026, 1, 12)
        )
        assert inv.line_items.count() == 2
        assert inv.invoice_type == "sales"
        assert inv.party_name == "Client A"
        assert inv.against_sales_order_id == sales_order.pk

    def test_invoice_total_matches_order_grand_total(self, sales_order):
        inv = Invoice.create_from_sales_order(
            sales_order, invoice_number="INV-FROM-SO-2", invoice_date=date(2026, 1, 12)
        )
        sales_order.refresh_from_db()
        assert inv.total == sales_order.grand_total

    def test_order_discount_carries_over(self, company, customer, item):
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-DISC-1",
            transaction_date=date(2026, 1, 10), status="Submitted", discount=Decimal("50"),
        )
        SalesOrderItem.objects.create(sales_order=so, item=item, qty=2, rate=100)
        so.recalculate_totals()
        so.refresh_from_db()
        inv = Invoice.create_from_sales_order(
            so, invoice_number="INV-DISC-1", invoice_date=date(2026, 1, 12)
        )
        assert inv.discount == Decimal("50.00")
        assert inv.total == so.grand_total == Decimal("150.00")

    def test_billed_amount_and_per_billed_tracked(self, sales_order):
        inv = Invoice.create_from_sales_order(
            sales_order, invoice_number="INV-FROM-SO-3", invoice_date=date(2026, 1, 12)
        )
        sales_order.refresh_from_db()
        assert sales_order.billed_amount == inv.total
        assert sales_order.per_billed == Decimal("100.00")

    def test_draft_order_cannot_be_invoiced(self, sales_order):
        sales_order.status = "Draft"
        sales_order.save()
        with pytest.raises(ValidationError):
            Invoice.create_from_sales_order(
                sales_order, invoice_number="INV-DRAFT-1", invoice_date=date(2026, 1, 12)
            )

    def test_duplicate_invoice_number_rejected(self, sales_order):
        Invoice.create_from_sales_order(
            sales_order, invoice_number="INV-DUP-1", invoice_date=date(2026, 1, 12)
        )
        with pytest.raises(ValidationError):
            Invoice.create_from_sales_order(
                sales_order, invoice_number="INV-DUP-1", invoice_date=date(2026, 1, 12)
            )

    def test_order_with_no_lines_rejected(self, company, customer):
        so = SalesOrder.objects.create(
            company=company, customer=customer, so_number="SO-EMPTY-1",
            transaction_date=date(2026, 1, 10), status="Submitted",
        )
        with pytest.raises(ValidationError):
            Invoice.create_from_sales_order(
                so, invoice_number="INV-EMPTY-1", invoice_date=date(2026, 1, 12)
            )

    def test_api_action_creates_invoice(self, auth_client, sales_order):
        resp = auth_client.post(
            f"/api/selling/sales-orders/{sales_order.pk}/create_invoice/",
            {"invoice_number": "INV-API-1", "invoice_date": "2026-01-12"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(resp.data["line_items"]) == 2

    def test_api_action_requires_invoice_number(self, auth_client, sales_order):
        resp = auth_client.post(
            f"/api/selling/sales-orders/{sales_order.pk}/create_invoice/", {}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.fixture
def purchase_order(company, supplier, branch, warehouse, item):
    po = PurchaseOrder.objects.create(
        company=company, supplier=supplier, po_number="PO-CONV-1",
        transaction_date=date(2026, 1, 10), branch=branch, warehouse=warehouse,
        status="Submitted",
    )
    PurchaseOrderItem.objects.create(purchase_order=po, item=item, qty=4, rate=100)
    PurchaseTaxCharge.objects.create(purchase_order=po, tax_rate=15, tax_amount=Decimal("60"))
    po.recalculate_totals()
    po.refresh_from_db()
    return po


@pytest.mark.django_db
class TestPurchaseOrderToInvoice:
    def test_conversion_copies_lines_and_totals(self, purchase_order):
        inv = Invoice.create_from_purchase_order(
            purchase_order, invoice_number="INV-FROM-PO-1", invoice_date=date(2026, 1, 12)
        )
        purchase_order.refresh_from_db()
        assert inv.invoice_type == "purchase"
        assert inv.party_name == "Vendor B"
        assert inv.line_items.count() == 1
        assert inv.total == purchase_order.grand_total
        assert purchase_order.billed_amount == inv.total

    def test_api_action_creates_invoice(self, auth_client, purchase_order):
        resp = auth_client.post(
            f"/api/buying/purchase-orders/{purchase_order.pk}/create_invoice/",
            {"invoice_number": "INV-PO-API-1", "invoice_date": "2026-01-12"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["invoice_type"] == "purchase"
