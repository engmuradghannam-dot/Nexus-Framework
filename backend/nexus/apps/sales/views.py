from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Backorder, Delivery, Invoice, Quotation, SalesOrder, SalesOrderItem
from .serializers import (
    BackorderSerializer,
    DeliverySerializer,
    InvoiceSerializer,
    QuotationSerializer,
    SalesOrderItemSerializer,
    SalesOrderSerializer,
)


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related('customer', 'warehouse').all()
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        # SAL-CTRL-001 Credit Check + SAL-CTRL-002 Stock Availability + SAL-RULE-002 Stock Reservation
        order = self.get_object()
        if not order.check_credit():
            return Response({"error": "Order blocked: customer exceeds credit limit"}, status=status.HTTP_400_BAD_REQUEST)
        shortages = order.reserve_stock()
        if shortages:
            return Response({"error": "Insufficient stock", "products": shortages}, status=status.HTTP_400_BAD_REQUEST)
        for item in order.items.all():
            from nexus.apps.industry.models import Inventory
            inventory = Inventory.objects.filter(product=item.product, warehouse=order.warehouse).first()
            if inventory:
                inventory.reserve(item.quantity)
        order.calculate_tax()
        order.status = 'confirmed'
        order.save()
        return Response({"status": "confirmed"})

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        # SAL-RULE-001 Auto Invoice Generation on delivery
        order = self.get_object()
        order.status = 'delivered'
        order.save()
        invoice, created = Invoice.objects.get_or_create(
            order=order,
            defaults={'total_amount': order.total_amount + order.tax_amount - order.discount_amount},
        )
        return Response({"status": "delivered", "invoice_id": invoice.invoice_id})


class SalesOrderItemViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderItem.objects.select_related('order', 'product').all()
    serializer_class = SalesOrderItemSerializer
    permission_classes = [IsAuthenticated]


class BackorderViewSet(viewsets.ModelViewSet):
    queryset = Backorder.objects.select_related('order_item').all()
    serializer_class = BackorderSerializer
    permission_classes = [IsAuthenticated]


class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.select_related('order').all()
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.select_related('customer').all()
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related('order').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
