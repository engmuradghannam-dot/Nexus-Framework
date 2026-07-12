from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DepreciableAsset
from .serializers import DepreciableAssetSerializer
from apps.tenants.mixins import TenantScopedMixin


class DepreciableAssetViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = DepreciableAsset.objects.all()
    serializer_class = DepreciableAssetSerializer

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        asset = self.get_object()
        return Response({"asset": self.get_serializer(asset).data, "schedule": asset.schedule()})
