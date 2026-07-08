from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Branch, Warehouse
from .serializers import UserSerializer, BranchSerializer, WarehouseSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'permissions_level', 'is_department_head', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'department']
    ordering_fields = ['created_at', 'email', 'permissions_level']

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.prefetch_related('warehouses')
    serializer_class = BranchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'address']

    @action(detail=True, methods=['get'])
    def warehouses(self, request, pk=None):
        branch = self.get_object()
        warehouses = branch.warehouses.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return Response(serializer.data)


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.select_related('branch', 'parent_warehouse')
    serializer_class = WarehouseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['branch', 'parent_warehouse', 'is_active']
    search_fields = ['name', 'code']

    @action(detail=False, methods=['get'])
    def low_capacity(self, request):
        threshold = request.query_params.get('threshold', 90)
        warehouses = [w for w in Warehouse.objects.all() if w.occupancy_rate >= float(threshold)]
        serializer = self.get_serializer(warehouses, many=True)
        return Response(serializer.data)
