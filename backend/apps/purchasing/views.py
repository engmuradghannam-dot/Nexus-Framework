from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .models import PurchaseDoc
from .serializers import PurchaseDocSerializer


class PurchaseDocViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = PurchaseDoc.objects.all()
    serializer_class = PurchaseDocSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["doc_type", "status"]

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        doc = self.get_object()
        ok, msg, ref = doc.process()
        return Response({"success": ok, "message": msg, "linked_ref": ref,
                         "document": self.get_serializer(doc).data}, status=200 if ok else 400)
