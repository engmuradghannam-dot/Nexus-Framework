from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TradeDoc
from .serializers import TradeDocSerializer


class TradeDocViewSet(viewsets.ModelViewSet):
    queryset = TradeDoc.objects.all()
    serializer_class = TradeDocSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["doc_type", "status"]

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        doc = self.get_object()
        ok, msg = doc.process()
        return Response(
            {"success": ok, "message": msg, "document": self.get_serializer(doc).data},
            status=200 if ok else 400,
        )
