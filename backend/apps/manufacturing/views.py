from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.exceptions import PermissionDenied

from apps.core.mixins import CompanyScopedMixin

from .models import (
    BOM,
    BOMItem,
    JobCard,
    MaterialReservation,
    ProductionBatch,
    QualityInspection,
    QualityInspectionParameter,
    ScheduleSlot,
    WorkOrder,
    Workstation,
)
from .serializers import (
    BOMItemSerializer,
    BOMSerializer,
    JobCardSerializer,
    ProductionBatchSerializer,
    QualityInspectionParameterSerializer,
    QualityInspectionSerializer,
    ScheduleSlotSerializer,
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


    @action(detail=True, methods=["get"])
    def material_requirements(self, request, pk=None):
        """MFG-RULE-001: explode the BOM for this order's quantity."""
        wo = self.get_object()
        try:
            reqs = wo.material_requirements()
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        rows = []
        for line, required in reqs:
            available = (
                line.item.stock_in_warehouse(wo.warehouse) if wo.warehouse else None
            )
            reserved = (
                line.item.reserved_qty(wo.warehouse, exclude_work_order=wo)
                if wo.warehouse else None
            )
            rows.append({
                "item_code": line.item.item_code,
                "item_name": line.item.item_name,
                "required": str(required),
                "available": str(available) if available is not None else None,
                "reserved_elsewhere": str(reserved) if reserved is not None else None,
                "short": (available - reserved < required) if available is not None else None,
            })
        return Response({"work_order": wo.wo_number, "requirements": rows})

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        """MFG-CTRL-001 + MFG-CTRL-003 + MFG-RULE-002."""
        wo = self.get_object()
        try:
            ok, message = wo.release()
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": ok, "message": message,
                         "reserved": wo.reservations.count()})

    @action(detail=True, methods=["post"])
    def produce_batch(self, request, pk=None):
        """Produce a traced, potency-adjusted batch from this work order.

        Body: {output_batch_no, output_qty?, inputs: {bom_item_id: {batch_no,
        potency}}}. Consumes the named input batches (scaling potency-managed
        lines by each batch's assay) and records the full genealogy.
        """
        wo = self.get_object()
        output_batch_no = request.data.get("output_batch_no")
        if not output_batch_no:
            return Response({"detail": "output_batch_no is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        raw_inputs = request.data.get("inputs", {})
        # Normalise {id: {batch_no, potency}} into {int id: (batch_no, potency)}.
        input_batches = {}
        for key, spec in raw_inputs.items():
            try:
                bom_item_id = int(key)
            except (TypeError, ValueError):
                return Response({"detail": f"Invalid BOM item id '{key}'."},
                                status=status.HTTP_400_BAD_REQUEST)
            input_batches[bom_item_id] = (spec.get("batch_no"), spec.get("potency", 100))
        try:
            pb = wo.produce_batch(
                output_batch_no, input_batches,
                output_qty=request.data.get("output_qty"),
            )
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductionBatchSerializer(pb).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def production_batches(self, request):
        """All traced batches for the scoped company."""
        qs = ProductionBatch.objects.filter(
            work_order__in=self.get_queryset()
        ).prefetch_related("consumptions__input_item").select_related("output_item", "work_order")
        return Response(ProductionBatchSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def yield_report(self, request, pk=None):
        """MFG-RULE-003 + MFG-CTRL-004."""
        wo = self.get_object()
        return Response({
            "planned": str(wo.qty_to_produce),
            "produced": str(wo.produced_qty),
            "scrap": str(wo.scrap_qty),
            "yield_percent": str(wo.yield_percent) if wo.yield_percent is not None else None,
            "variance_exceeded": wo.yield_variance_exceeded,
            "effective_unit_cost": str(wo.effective_unit_cost),
        })

class BOMViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item", "is_active", "company"]
    company_field = "company"


    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """MFG-CTRL-001: sign off a BOM so production can release against it."""
        from apps.hr.models import Employee

        bom = self.get_object()
        try:
            employee = Employee.objects.get(pk=request.data.get("employee"))
        except (Employee.DoesNotExist, TypeError, ValueError):
            return Response({"detail": "A valid employee is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        bom.approve(employee)
        return Response({"approved": True, "approved_at": bom.approved_at})

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


class ProductionBatchViewSet(CompanyScopedMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only view of traced production batches, with genealogy.

    Filterable by output_batch_no and output_item, so a recall can start from a
    finished batch and read its inputs, or search by an input batch to find
    every finished batch that consumed it (via the consumptions relation).
    """

    queryset = ProductionBatch.objects.prefetch_related(
        "consumptions__input_item"
    ).select_related("output_item", "work_order")
    serializer_class = ProductionBatchSerializer
    company_field = "company"
    filterset_fields = ["output_item", "output_batch_no", "work_order", "company"]

    @action(detail=False, methods=["get"])
    def containing_batch(self, request):
        """Forward trace for recalls: every production batch that consumed a
        given input batch. Query: ?item=<id>&batch_no=<no>."""
        item_id = request.query_params.get("item")
        batch_no = request.query_params.get("batch_no")
        if not batch_no:
            return Response({"detail": "batch_no is required."},
                            status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(consumptions__input_batch_no=batch_no)
        if item_id:
            qs = qs.filter(consumptions__input_item_id=item_id)
        qs = qs.distinct()
        return Response(self.get_serializer(qs, many=True).data)


class ScheduleSlotViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """Finite-capacity scheduling: book work orders on workstations without
    overlaps, and ask for the earliest free window."""

    queryset = ScheduleSlot.objects.select_related("workstation", "work_order")
    serializer_class = ScheduleSlotSerializer
    company_field = "company"
    filterset_fields = ["workstation", "work_order", "status", "company"]

    @action(detail=False, methods=["get"])
    def earliest_free(self, request):
        """The earliest free window on a station. Query: ?workstation=<id>
        &minutes=<n>&not_before=<iso>. Defaults not_before to now."""
        from datetime import timedelta
        from django.utils import timezone
        from django.utils.dateparse import parse_datetime

        ws_id = request.query_params.get("workstation")
        minutes = request.query_params.get("minutes")
        if not ws_id or not minutes:
            return Response({"detail": "workstation and minutes are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        ws = Workstation.objects.filter(pk=ws_id).first()
        if ws is None:
            return Response({"detail": "workstation not found."},
                            status=status.HTTP_404_NOT_FOUND)
        nb_raw = request.query_params.get("not_before")
        not_before = parse_datetime(nb_raw) if nb_raw else timezone.now()
        start = ScheduleSlot.earliest_free_window(ws, timedelta(minutes=int(minutes)), not_before)
        return Response({"workstation": ws.code, "earliest_start": start.isoformat()})
