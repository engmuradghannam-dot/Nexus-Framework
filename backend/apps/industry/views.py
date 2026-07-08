from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Sector, Company, Metric
from .serializers import SectorSerializer, CompanySerializer, MetricSerializer


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.prefetch_related('sub_sectors', 'companies')
    serializer_class = SectorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'parent_sector']
    search_fields = ['name', 'code']


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.select_related('sector').prefetch_related('metrics')
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sector', 'is_active']
    search_fields = ['name', 'ticker', 'headquarters']
    ordering_fields = ['market_cap', 'revenue', 'employees', 'created_at']

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        top = self.get_queryset().order_by('-market_cap')[:10]
        serializer = self.get_serializer(top, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        company = self.get_object()
        metrics = company.metrics.all()
        serializer = MetricSerializer(metrics, many=True)
        return Response(serializer.data)


class MetricViewSet(viewsets.ModelViewSet):
    queryset = Metric.objects.select_related('company')
    serializer_class = MetricSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['company', 'metric_type', 'period']
    search_fields = ['name', 'period']
