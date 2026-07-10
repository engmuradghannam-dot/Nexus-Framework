from rest_framework import viewsets

from apps.core.mixins import CompanyScopedMixin, LockAfterSubmitMixin

from .models import Customer, SalesOrder, SalesOrderItem, SalesPayment, SalesTaxCharge
from .serializers import (
    CustomerSerializer,
    SalesOrderItemSerializer,
    SalesOrderSerializer,
    SalesPaymentSerializer,
    SalesTaxChargeSerializer,
)


class CustomerViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    company_field = "company"


class SalesOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    company_field = "company"


class SalesOrderItemViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    filterset_fields = ["sales_order", "item"]
    company_field = "sales_order__company"
    parent_field = "sales_order"


class SalesTaxChargeViewSet(
    LockAfterSubmitMixin, CompanyScopedMixin, viewsets.ModelViewSet
):
    queryset = SalesTaxCharge.objects.all()
    serializer_class = SalesTaxChargeSerializer
    filterset_fields = ["sales_order"]
    company_field = "sales_order__company"
    parent_field = "sales_order"


class SalesPaymentViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = SalesPayment.objects.all()
    serializer_class = SalesPaymentSerializer
    filterset_fields = ["sales_order"]
    company_field = "sales_order__company"
