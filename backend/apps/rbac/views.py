from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import ACTIONS, Role, RoleAssignment, user_can
from .serializers import RoleAssignmentSerializer, RoleSerializer

MODULES = [
    ("dashboard", "لوحة المعلومات"), ("pmo", "إدارة المشاريع"), ("crm", "إدارة العملاء"),
    ("selling", "المبيعات"), ("buying", "المشتريات"), ("inventory", "المخزون"),
    ("warehouses", "المستودعات"), ("reorder", "إعادة الطلب"), ("manufacturing", "التصنيع"),
    ("assets", "الأصول"), ("hr", "الموارد البشرية"), ("accounting", "المحاسبة"),
    ("invoicing", "الفواتير"), ("taxes", "الضرائب"), ("controls", "مكتبة الضوابط"),
    ("regulatory", "الامتثال"), ("company-setup", "إعداد الشركة"), ("users", "المستخدمين"),
    ("audit", "سجل التدقيق"), ("settings", "الإعدادات"),
]


class RoleViewSet(viewsets.ModelViewSet):
    """Roles are a shared, global catalog (no per-company scoping concept
    exists for RBAC). Any authenticated user may read them (needed to
    render a permission matrix), but only a superuser may create/edit/
    delete one — editing a Role's `permissions` JSON changes what every
    user holding that role can do system-wide."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=["get"])
    def catalog(self, request):
        """The modules and actions available to build a permission matrix."""
        return Response({
            "modules": [{"key": k, "label": l} for k, l in MODULES],
            "actions": ACTIONS,
        })

    @action(detail=False, methods=["get"])
    def my_permissions(self, request):
        """The effective module permissions for the current user."""
        u = request.user
        if u.is_superuser:
            perms = {k: list(ACTIONS) for k, _ in MODULES}
        else:
            perms = {}
            for a in RoleAssignment.objects.filter(user=u).select_related("role"):
                for module, acts in (a.role.permissions or {}).items():
                    perms[module] = sorted(set(perms.get(module, [])) | set(acts))
        return Response({"is_superuser": u.is_superuser, "permissions": perms})


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    """Who holds which role. A regular user may only ever see their own
    assignments (use the `my_permissions` action on RoleViewSet for the
    effective-permissions view); granting/revoking a role is a superuser-only
    action, since there's no company-scoped notion of "admin" for RBAC."""

    queryset = RoleAssignment.objects.select_related("role", "user").all()
    serializer_class = RoleAssignmentSerializer
    filterset_fields = ["user", "role"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return qs
        return qs.filter(user=user)
