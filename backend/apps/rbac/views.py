from rest_framework import viewsets
from rest_framework.decorators import action
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
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

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
    queryset = RoleAssignment.objects.select_related("role", "user").all()
    serializer_class = RoleAssignmentSerializer
    filterset_fields = ["user", "role"]
