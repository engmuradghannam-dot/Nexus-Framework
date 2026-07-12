from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.audit.models import record_audit
from apps.rbac.models import RoleAssignment, user_can
from apps.tenants.mixins import TenantScopedMixin

from .models import ModuleRecord
from .serializers import ModuleRecordSerializer


class ModuleRecordViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = ModuleRecord.objects.all()
    serializer_class = ModuleRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module"]

    def _enforce(self, module_action, module):
        """RBAC on writes. Superusers bypass; users with NO roles are
        grandfathered (not locked out); users WITH roles are enforced."""
        u = self.request.user
        if u.is_superuser:
            return
        if not RoleAssignment.objects.filter(user=u).exists():
            return
        if not user_can(u, module, module_action):
            raise PermissionDenied(f"لا تملك صلاحية {module_action} على {module}")

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
        module = serializer.validated_data.get("module", "")
        self._enforce("create", module)
        user = self.request.user if self.request.user.is_authenticated else None
        tenant = getattr(user, "tenant", None) if user else None
        if tenant is not None:
            obj = serializer.save(created_by=user, tenant=tenant)
        else:
            obj = serializer.save(created_by=user)
        record_audit(self.request, "create", obj.module, obj.pk, obj.data)

    def perform_update(self, serializer):
        self._enforce("edit", serializer.instance.module)
        obj = serializer.save()
        record_audit(self.request, "update", obj.module, obj.pk, obj.data)

    def perform_destroy(self, instance):
        self._enforce("delete", instance.module)
        record_audit(self.request, "delete", instance.module, instance.pk, instance.data)
        instance.delete()
