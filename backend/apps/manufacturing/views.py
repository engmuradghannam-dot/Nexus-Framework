from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import BOM, WorkOrder
from .serializers import BOMSerializer, WorkOrderSerializer

class BOMViewSet(viewsets.ModelViewSet):
    queryset = BOM.objects.all()
    serializer_class = BOMSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['bom_name', 'item__item_name']
    filterset_fields = ['company', 'is_active']

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['wo_number', 'item_to_manufacture__item_name']
    filterset_fields = ['status', 'company']
