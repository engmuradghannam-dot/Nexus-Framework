from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import record_audit

from .models import ModuleRecord
from .serializers import ModuleRecordSerializer


class ModuleRecordViewSet(viewsets.ModelViewSet):
    queryset = ModuleRecord.objects.all()
    serializer_class = ModuleRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module"]


    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Inventory items at or below their reorder level (auto-reorder alert)."""
        items = ModuleRecord.objects.filter(module="inventory")
        alerts = []
        for r in items:
            d = r.data or {}
            try:
                current = float(d.get("current_stock") or 0)
                reorder = float(d.get("reorder_level") or 0)
            except (TypeError, ValueError):
                continue
            if reorder > 0 and current <= reorder:
                max_stock = float(d.get("max_stock") or reorder)
                alerts.append({
                    "id": r.id,
                    "item_code": d.get("item_code", ""),
                    "name": d.get("arabic_name") or d.get("english_name", ""),
                    "warehouse": d.get("warehouse", ""),
                    "current_stock": current,
                    "reorder_level": reorder,
                    "suggested_order_qty": max(max_stock - current, 0),
                })
        return Response({"count": len(alerts), "alerts": alerts})

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        obj = serializer.save(created_by=user)
        record_audit(self.request, "create", obj.module, obj.pk, obj.data)

    def perform_update(self, serializer):
        obj = serializer.save()
        record_audit(self.request, "update", obj.module, obj.pk, obj.data)

    def perform_destroy(self, instance):
        record_audit(self.request, "delete", instance.module, instance.pk, instance.data)
        instance.delete()
