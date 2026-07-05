from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .models import AssetCategory, Asset
from .serializers import AssetCategorySerializer, AssetSerializer

class AssetCategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    filter_backends = [SearchFilter]
    search_fields = ['name']

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['asset_name', 'asset_code']
    filterset_fields = ['status', 'category', 'company']
