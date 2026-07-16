from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import IndustrySector, Product, Inventory, Supplier, PurchaseOrder, PurchaseOrderItem
from .serializers import (
    IndustrySectorSerializer, ProductSerializer, InventorySerializer,
    SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer
)

class IndustrySectorViewSet(viewsets.ModelViewSet):
    queryset = IndustrySector.objects.all()
    serializer_class = IndustrySectorSerializer
    permission_classes = [IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_sector(self, request):
        sector_id = request.query_params.get('sector_id')
        if sector_id:
            products = Product.objects.filter(sector_id=sector_id)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response({"error": "sector_id required"}, status=status.HTTP_400_BAD_REQUEST)

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_warehouse(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            inventory = Inventory.objects.filter(warehouse_id=warehouse_id)
            serializer = self.get_serializer(inventory, many=True)
            return Response(serializer.data)
        return Response({"error": "warehouse_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def needs_reorder(self, request):
        """Get all inventory items that need reordering."""
        inventory = [inv for inv in Inventory.objects.all() if inv.needs_reorder]
        serializer = self.get_serializer(inventory, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_reorder(self, request, pk=None):
        """Create a purchase order for reorder."""
        inventory = self.get_object()
        supplier_id = request.data.get('supplier_id')

        if not supplier_id:
            return Response({"error": "supplier_id required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)

        order = PurchaseOrder.objects.create(
            supplier=supplier,
            warehouse=inventory.warehouse,
            status='draft'
        )

        PurchaseOrderItem.objects.create(
            order=order,
            product=inventory.product,
            quantity=inventory.reorder_quantity,
            unit_price=inventory.product.unit_price
        )

        inventory.last_reorder_date = __import__('datetime').date.today()
        inventory.save()

        return Response({
            "status": "reorder created",
            "order_id": order.id,
            "quantity": inventory.reorder_quantity
        })

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_status(self, request):
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = PurchaseOrder.objects.filter(status=status_filter)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        return Response({"error": "status required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        order.status = 'confirmed'
        order.save()
        return Response({"status": "order confirmed"})

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        order = self.get_object()
        order.status = 'received'
        order.save()

        # Update inventory
        for item in order.items.all():
            inv, created = Inventory.objects.get_or_create(
                product=item.product,
                warehouse=order.warehouse,
                defaults={'quantity': 0, 'min_reorder_level': 10, 'reorder_quantity': 50}
            )
            inv.quantity += item.quantity
            inv.save()

        return Response({"status": "order received, inventory updated"})

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticated]
