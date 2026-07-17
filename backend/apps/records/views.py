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

    def _scoped_items(self):
        """Low-stock Items visible to the requesting user, scoped fail-closed.

        These actions reach straight into apps.inventory.Item rather than the
        ViewSet's own (tenant-scoped) ModuleRecord queryset, so none of the
        surrounding scoping applies to them automatically. Without this an
        authenticated user of company A could read — and, via
        create_purchase_orders, write POs against — every other company in the
        installation. Mirrors CompanyScopedMixin: superusers bypass, anonymous
        or company-less users get nothing.
        """
        from apps.inventory.models import Item

        items = Item.objects.filter(is_stock_item=True, is_active=True, reorder_level__gt=0)
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return items.none()
        if user.is_superuser:
            return items
        return items.filter(company__in=user.managed_companies.all())

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
        """Real stock items at or below their reorder level (auto-reorder alert).

        Was previously reading from ModuleRecord (a generic freeform-JSON
        store unrelated to real inventory) instead of apps.inventory.Item,
        so it never reflected actual stock movements from Buying/Selling/
        Manufacturing -- this alert list was permanently stale/disconnected
        from the real system.
        """
        items = self._scoped_items()
        if request.query_params.get("company"):
            items = items.filter(company_id=request.query_params["company"])

        alerts = []
        for item in items:
            current = item.stock_quantity
            if current > item.reorder_level:
                continue
            suggested = item.reorder_qty if item.reorder_qty > 0 else max(item.reorder_level - current, 0)
            alerts.append({
                "id": item.id,
                "item_code": item.item_code,
                "name": item.item_name,
                "supplier": item.supplier_id,
                "supplier_name": getattr(item.supplier, "name", ""),
                "current_stock": float(current),
                "reorder_level": float(item.reorder_level),
                "suggested_order_qty": float(suggested),
            })
        return Response({"count": len(alerts), "alerts": alerts})

    @action(detail=False, methods=["post"])
    def create_purchase_orders(self, request):
        """Auto-generate draft Purchase Orders from low-stock items, one PO
        per supplier (items with no supplier set are skipped and reported).
        Pass {"item_ids": [...]} to restrict to a subset of low-stock items;
        omit to act on every item currently below its reorder level."""
        from datetime import date

        from django.db import transaction

        from apps.buying.models import PurchaseOrder, PurchaseOrderItem

        item_ids = request.data.get("item_ids")
        items = self._scoped_items()
        if item_ids:
            items = items.filter(pk__in=item_ids)

        by_supplier = {}
        skipped = []
        for item in items:
            current = item.stock_quantity
            if current > item.reorder_level:
                continue
            if not item.supplier_id:
                skipped.append(item.item_code)
                continue
            by_supplier.setdefault(item.supplier_id, []).append(item)

        def next_po_number():
            # po_number is globally unique, so a per-company counter collides as
            # soon as two companies reach the same PO count in the same month.
            prefix = f"PO-AUTO-{date.today():%Y%m}-"
            seq = PurchaseOrder.objects.filter(po_number__startswith=prefix).count() + 1
            while PurchaseOrder.objects.filter(po_number=f"{prefix}{seq:04d}").exists():
                seq += 1
            return f"{prefix}{seq:04d}"

        created = []
        for supplier_id, supplier_items in by_supplier.items():
            company = supplier_items[0].company
            with transaction.atomic():
                po = PurchaseOrder.objects.create(
                    company=company, supplier_id=supplier_id,
                    po_number=next_po_number(),
                    transaction_date=date.today(),
                    notes="تم الإنشاء تلقائياً من تنبيهات إعادة الطلب / Auto-generated from reorder alerts",
                )
                for item in supplier_items:
                    qty = item.reorder_qty if item.reorder_qty > 0 else max(item.reorder_level - item.stock_quantity, 0)
                    if qty <= 0:
                        continue
                    PurchaseOrderItem.objects.create(
                        purchase_order=po, item=item, qty=qty, rate=item.standard_rate,
                    )
            created.append(po.po_number)

        return Response({"created": created, "skipped_no_supplier": skipped})

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
