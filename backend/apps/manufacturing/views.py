from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from apps.core.mixins import CompanyScopedMixin

from .models import BOM, BOMItem, WorkOrder
from .serializers import BOMItemSerializer, BOMSerializer, WorkOrderSerializer


class WorkOrderViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Status transitions (Draft -> In Progress -> Completed/Cancelled) go
    through a normal PATCH of `status`; WorkOrderSerializer validates the
    transition and triggers `complete_production()` as a side effect. There
    used to be separate start/complete/cancel actions here, but they
    duplicated (and bypassed the company scoping and transition validation
    of) that same path, and `complete` referenced a field that doesn't
    exist on Item — removed rather than fixed in place."""

    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "bom", "company"]
    company_field = "company"


class BOMViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item", "is_active", "company"]
    company_field = "company"


class BOMItemViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOMItem.objects.all()
    serializer_class = BOMItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["bom", "item"]
    company_field = "bom__company"
