from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.exceptions import PermissionDenied

from apps.core.mixins import CompanyScopedMixin

from .models import BOM, BOMItem, JobCard, QualityInspection, QualityInspectionParameter, WorkOrder
from .serializers import (
    BOMItemSerializer,
    BOMSerializer,
    JobCardSerializer,
    QualityInspectionParameterSerializer,
    QualityInspectionSerializer,
    WorkOrderSerializer,
)


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


class JobCardViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = JobCard.objects.all()
    serializer_class = JobCardSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["work_order", "status", "employee", "company"]
    company_field = "company"

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        job_card = self.get_object()
        ok, msg = job_card.start()
        return Response({"success": ok, "message": msg, "job_card": self.get_serializer(job_card).data},
                        status=200 if ok else 400)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        job_card = self.get_object()
        ok, msg = job_card.complete(completed_qty=request.data.get("completed_qty"))
        return Response({"success": ok, "message": msg, "job_card": self.get_serializer(job_card).data},
                        status=200 if ok else 400)


class QualityInspectionViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Locks a QualityInspection against edits once it's Accepted/Rejected —
    an inspection result shouldn't be quietly rewritten after the fact."""

    queryset = QualityInspection.objects.all()
    serializer_class = QualityInspectionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item", "inspection_type", "status", "company", "reference_work_order", "reference_purchase_order"]
    company_field = "company"
    editable_statuses = ("Pending",)

    def _assert_editable(self, instance):
        if instance.status not in self.editable_statuses:
            raise PermissionDenied(f"Cannot modify: inspection is '{instance.status}' (locked).")

    def perform_update(self, serializer):
        self._assert_editable(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_editable(instance)
        instance.delete()


class QualityInspectionParameterViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = QualityInspectionParameter.objects.all()
    serializer_class = QualityInspectionParameterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["inspection"]
    company_field = "inspection__company"
