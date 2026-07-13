from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import CustomField
from .serializers import CustomFieldSerializer


class CustomFieldViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = CustomField.objects.filter(is_active=True)
    serializer_class = CustomFieldSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module"]
    pagination_class = None

    @action(detail=False, methods=["get"])
    def modules(self, request):
        """Distinct modules that have custom fields defined."""
        qs = self.filter_queryset(self.get_queryset())
        return Response(sorted(set(qs.values_list("module", flat=True))))
