from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import StockMovement, valuate
from .serializers import StockMovementSerializer


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item_code", "warehouse", "movement_type"]

    @action(detail=False, methods=["get"])
    def valuation(self, request):
        """Inventory valuation per item under FIFO / LIFO / Moving Average."""
        codes = (
            StockMovement.objects.order_by("item_code")
            .values_list("item_code", flat=True)
            .distinct()
        )
        rows = []
        totals = {"fifo_value": 0.0, "lifo_value": 0.0, "moving_avg_value": 0.0}
        for code in codes:
            movs = list(StockMovement.objects.filter(item_code=code).order_by("date", "id"))
            name = movs[0].item_name if movs else ""
            v = valuate(movs)
            for k in totals:
                totals[k] += v[k]
            rows.append({"item_code": code, "item_name": name, **v})
        rows.sort(key=lambda r: r["item_code"])
        return Response({
            "rows": rows,
            "totals": {k: round(val, 2) for k, val in totals.items()},
        })
