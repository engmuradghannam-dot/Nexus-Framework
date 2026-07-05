from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import Customer, SalesOrder
from .serializers import CustomerSerializer, SalesOrderSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name', 'email', 'tax_id']
    filterset_fields = ['company', 'is_active']

class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['so_number', 'customer__name']
    filterset_fields = ['status', 'company', 'customer']
