from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import StockMovement, valuate
from .serializers import StockMovementSerializer
from apps.tenants.mixins import TenantScopedMixin


class StockMovementViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["item_code", "warehouse", "movement_type"]

    @action(detail=False, methods=["post"])
    def transfer(self, request):
        """Transfer stock between warehouses: OUT of source + IN to destination."""
        d = request.data
        try:
            qty = float(d.get("quantity") or 0)
        except (TypeError, ValueError):
            qty = 0
        code = d.get("item_code", "")
        src = d.get("from_warehouse", "")
        dst = d.get("to_warehouse", "")
        if qty <= 0 or not code or not src or not dst:
            return Response({"success": False, "message": "أدخل الصنف والكمية والمستودعين"}, status=400)
        if src == dst:
            return Response({"success": False, "message": "المستودع المصدر والوجهة متطابقان"}, status=400)
        from datetime import date as _date
        name = d.get("item_name", "")
        cost = d.get("unit_cost") or 0
        day = d.get("date") or _date.today().isoformat()
        ref = f"نقل {src}→{dst}"
        tenant = getattr(request.user, "tenant", None)
        StockMovement.objects.create(item_code=code, item_name=name, warehouse=src,
            movement_type="out", quantity=qty, unit_cost=cost, date=day, reference=ref, tenant=tenant)
        StockMovement.objects.create(item_code=code, item_name=name, warehouse=dst,
            movement_type="in", quantity=qty, unit_cost=cost, date=day, reference=ref, tenant=tenant)
        return Response({"success": True, "message": f"تم نقل {qty} من {src} إلى {dst}"})

    @action(detail=False, methods=["get"])
    def valuation(self, request):
        """Inventory valuation per item under FIFO / LIFO / Moving Average."""
        scoped = self.filter_queryset(self.get_queryset())
        codes = scoped.order_by("item_code").values_list("item_code", flat=True).distinct()
        rows = []
        totals = {"fifo_value": 0.0, "lifo_value": 0.0, "moving_avg_value": 0.0}
        for code in codes:
            movs = list(scoped.filter(item_code=code).order_by("date", "id"))
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
