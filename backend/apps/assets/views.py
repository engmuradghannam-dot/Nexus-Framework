from rest_framework import viewsets

from apps.core.mixins import CompanyScopedMixin

from .models import Asset, AssetCategory
from .serializers import AssetCategorySerializer, AssetSerializer


class AssetViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    company_field = "company"


class AssetCategoryViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    company_field = "company"
