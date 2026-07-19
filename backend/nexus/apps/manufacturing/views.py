from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
import uuid

from nexus.apps.api_infra.scoping import CompanyScopedViewSet
from .models import (
    WorkCenter, BOM, BOMItem, Routing, RoutingOperation,
    ManufacturingOrder, ManufacturingOrderOperation,
    MaterialRequisition, MaterialRequisitionItem
)
from .serializers import (
    WorkCenterSerializer, BOMSerializer, BOMItemSerializer,
    RoutingSerializer, RoutingOperationSerializer,
    ManufacturingOrderSerializer, ManufacturingOrderOperationSerializer,
    MaterialRequisitionSerializer, MaterialRequisitionItemSerializer
)


class WorkCenterViewSet(CompanyScopedViewSet):
    queryset = WorkCenter.objects.all()
    serializer_class = WorkCenterSerializer
    company_field = "company"

    @action(detail=False, methods=['get'])
    def active(self, request):
        centers = self.get_queryset().filter(status='active')
        return Response(self.get_serializer(centers, many=True).data)

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)
        centers = self.get_queryset().filter(branch_id=branch_id)
        return Response(self.get_serializer(centers, many=True).data)


class BOMViewSet(CompanyScopedViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    company_field = "product__company"

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)
        boms = self.get_queryset().filter(product_id=product_id)
        return Response(self.get_serializer(boms, many=True).data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        bom = self.get_object()
        component_id = request.data.get('component_id')
        quantity = request.data.get('quantity', 1)
        unit_cost = request.data.get('unit_cost', 0)
        scrap_percentage = request.data.get('scrap_percentage', 0)

        if not component_id:
            return Response({"error": "component_id required"}, status=status.HTTP_400_BAD_REQUEST)

        item, created = BOMItem.objects.get_or_create(
            bom=bom,
            component_id=component_id,
            defaults={
                'quantity': quantity,
                'unit_cost': unit_cost,
                'scrap_percentage': scrap_percentage
            }
        )
        if not created:
            item.quantity = quantity
            item.unit_cost = unit_cost
            item.scrap_percentage = scrap_percentage
            item.save()

        return Response(BOMItemSerializer(item).data)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        bom = self.get_object()
        product = bom.product
        # Unset other defaults for this product
        BOM.objects.filter(product=product, is_default=True).update(is_default=False)
        bom.is_default = True
        bom.save(update_fields=['is_default'])
        return Response({"status": "set as default"})


class BOMItemViewSet(CompanyScopedViewSet):
    queryset = BOMItem.objects.all()
    serializer_class = BOMItemSerializer
    company_field = "bom__product__company"


class RoutingViewSet(CompanyScopedViewSet):
    queryset = Routing.objects.all()
    serializer_class = RoutingSerializer
    company_field = "product__company"

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)
        routings = self.get_queryset().filter(product_id=product_id)
        return Response(self.get_serializer(routings, many=True).data)

    @action(detail=True, methods=['post'])
    def add_operation(self, request, pk=None):
        routing = self.get_object()
        sequence = request.data.get('sequence')
        name = request.data.get('name')
        work_center_id = request.data.get('work_center_id')
        setup_time = request.data.get('setup_time', 0)
        run_time_per_unit = request.data.get('run_time_per_unit', 0)

        if not name:
            return Response({"error": "name required"}, status=status.HTTP_400_BAD_REQUEST)

        op = RoutingOperation.objects.create(
            routing=routing,
            sequence=sequence or (routing.operations.count() + 1),
            name=name,
            work_center_id=work_center_id,
            setup_time=setup_time,
            run_time_per_unit=run_time_per_unit
        )
        return Response(RoutingOperationSerializer(op).data)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        routing = self.get_object()
        product = routing.product
        Routing.objects.filter(product=product, is_default=True).update(is_default=False)
        routing.is_default = True
        routing.save(update_fields=['is_default'])
        return Response({"status": "set as default"})


class RoutingOperationViewSet(CompanyScopedViewSet):
    queryset = RoutingOperation.objects.all()
    serializer_class = RoutingOperationSerializer
    company_field = "routing__product__company"


class ManufacturingOrderViewSet(CompanyScopedViewSet):
    queryset = ManufacturingOrder.objects.all()
    serializer_class = ManufacturingOrderSerializer
    company_field = "company"

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset().filter(status=status_filter)
        return Response(self.get_serializer(orders, many=True).data)

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({"error": "product_id required"}, status=status.HTTP_400_BAD_REQUEST)
        orders = self.get_queryset().filter(product_id=product_id)
        return Response(self.get_serializer(orders, many=True).data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        orders = self.get_queryset().filter(
            planned_end__lt=timezone.now(),
            status__in=['draft', 'planned', 'released', 'in_progress', 'on_hold']
        )
        return Response(self.get_serializer(orders, many=True).data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        orders = self.get_queryset()
        return Response({
            'total_orders': orders.count(),
            'draft': orders.filter(status='draft').count(),
            'in_progress': orders.filter(status='in_progress').count(),
            'completed': orders.filter(status='completed').count(),
            'cancelled': orders.filter(status='cancelled').count(),
            'overdue': orders.filter(
                planned_end__lt=timezone.now(),
                status__in=['draft', 'planned', 'released', 'in_progress', 'on_hold']
            ).count(),
            'total_quantity': sum(o.quantity for o in orders),
            'total_produced': sum(o.quantity_produced for o in orders),
            'avg_completion': sum(o.completion_percentage for o in orders) / orders.count() if orders.count() else 0,
        })

    @action(detail=True, methods=['post'])
    def release(self, request, pk=None):
        order = self.get_object()
        if order.status != 'planned':
            return Response({"error": "Only planned orders can be released"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'released'
        order.save(update_fields=['status'])
        return Response({"status": "released"})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['released', 'planned']:
            return Response({"error": "Order must be released or planned to start"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'in_progress'
        order.actual_start = timezone.now()
        order.save(update_fields=['status', 'actual_start'])
        return Response({"status": "started"})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if order.status != 'in_progress':
            return Response({"error": "Only in-progress orders can be completed"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'completed'
        order.actual_end = timezone.now()
        order.save(update_fields=['status', 'actual_end'])
        return Response({"status": "completed"})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status in ['completed', 'cancelled']:
            return Response({"error": "Cannot cancel completed or already cancelled orders"}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        return Response({"status": "cancelled"})

    @action(detail=True, methods=['post'])
    def produce(self, request, pk=None):
        order = self.get_object()
        quantity = request.data.get('quantity', 0)
        rejected = request.data.get('rejected', 0)

        if order.status != 'in_progress':
            return Response({"error": "Order must be in progress to produce"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order.quantity_produced += quantity
            order.quantity_rejected += rejected
            order.save(update_fields=['quantity_produced', 'quantity_rejected'])

        return Response({
            "status": "produced",
            "quantity_produced": order.quantity_produced,
            "quantity_rejected": order.quantity_rejected,
            "remaining": order.remaining_quantity,
            "completion": order.completion_percentage
        })

    @action(detail=True, methods=['post'])
    def create_from_bom(self, request, pk=None):
        """Create a manufacturing order from BOM with auto-populated operations"""
        order = self.get_object()
        if not order.bom:
            return Response({"error": "Order has no BOM"}, status=status.HTTP_400_BAD_REQUEST)

        # Create material requisition from BOM items
        requisition = MaterialRequisition.objects.create(
            requisition_number=f"MR-{uuid.uuid4().hex[:8].upper()}",
            manufacturing_order=order,
            warehouse=order.branch.warehouses.first() if order.branch else None,
            requested_by=request.user
        )

        for bom_item in order.bom.items.all():
            total_qty = bom_item.effective_quantity * order.quantity
            MaterialRequisitionItem.objects.create(
                requisition=requisition,
                product=bom_item.component,
                quantity_requested=total_qty,
                unit_cost=bom_item.unit_cost
            )

        # Create operations from routing
        if order.routing:
            for i, op in enumerate(order.routing.operations.all()):
                ManufacturingOrderOperation.objects.create(
                    manufacturing_order=order,
                    routing_operation=op,
                    sequence=op.sequence,
                    work_center=op.work_center
                )

        return Response({
            "status": "created_from_bom",
            "requisition_id": requisition.id,
            "requisition_number": requisition.requisition_number,
            "material_items": requisition.items.count(),
            "operations_created": order.operations.count()
        })


class ManufacturingOrderOperationViewSet(CompanyScopedViewSet):
    queryset = ManufacturingOrderOperation.objects.all()
    serializer_class = ManufacturingOrderOperationSerializer
    company_field = "manufacturing_order__company"

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        op = self.get_object()
        op.status = 'in_progress'
        op.run_start = timezone.now()
        op.save(update_fields=['status', 'run_start'])
        return Response({"status": "started"})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        op = self.get_object()
        quantity = request.data.get('quantity_produced', 0)
        rejected = request.data.get('quantity_rejected', 0)
        setup_time = request.data.get('setup_time', 0)
        run_time = request.data.get('run_time', 0)

        op.status = 'completed'
        op.run_end = timezone.now()
        op.quantity_produced = quantity
        op.quantity_rejected = rejected
        op.actual_setup_time = setup_time
        op.actual_run_time = run_time
        op.completed_by = request.user
        op.save()

        # Update parent order
        order = op.manufacturing_order
        order.quantity_produced += quantity
        order.quantity_rejected += rejected
        order.save(update_fields=['quantity_produced', 'quantity_rejected'])

        return Response({"status": "completed"})


class MaterialRequisitionViewSet(CompanyScopedViewSet):
    queryset = MaterialRequisition.objects.all()
    serializer_class = MaterialRequisitionSerializer
    company_field = "manufacturing_order__company"

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if not status_filter:
            return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)
        reqs = self.get_queryset().filter(status=status_filter)
        return Response(self.get_serializer(reqs, many=True).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != 'pending':
            return Response({"error": "Only pending requisitions can be approved"}, status=status.HTTP_400_BAD_REQUEST)
        req.status = 'approved'
        req.approved_by = request.user
        req.approved_at = timezone.now()
        req.save(update_fields=['status', 'approved_by', 'approved_at'])
        return Response({"status": "approved"})

    @action(detail=True, methods=['post'])
    def issue(self, request, pk=None):
        req = self.get_object()
        if req.status not in ['approved', 'partial']:
            return Response({"error": "Requisition must be approved or partially issued"}, status=status.HTTP_400_BAD_REQUEST)

        items_data = request.data.get('items', [])
        with transaction.atomic():
            for item_data in items_data:
                item_id = item_data.get('item_id')
                qty_issued = item_data.get('quantity_issued', 0)
                try:
                    item = req.items.get(id=item_id)
                    item.quantity_issued += qty_issued
                    item.save(update_fields=['quantity_issued'])
                except MaterialRequisitionItem.DoesNotExist:
                    pass

            # Check if fully issued
            all_fulfilled = all(item.fulfillment_percentage >= 100 for item in req.items.all())
            req.status = 'issued' if all_fulfilled else 'partial'
            req.save(update_fields=['status'])

        return Response({"status": req.status})


class MaterialRequisitionItemViewSet(CompanyScopedViewSet):
    queryset = MaterialRequisitionItem.objects.all()
    serializer_class = MaterialRequisitionItemSerializer
    company_field = "requisition__manufacturing_order__company"
