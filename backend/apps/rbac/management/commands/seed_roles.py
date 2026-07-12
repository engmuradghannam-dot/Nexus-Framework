"""Seed standard roles with per-module permissions (idempotent)."""
from django.core.management.base import BaseCommand

from apps.rbac.models import Role

ALL = ["view", "create", "edit", "delete"]
VIEW = ["view"]

ROLES = [
    ("Administrator", "مدير النظام", "صلاحية كاملة على كل الوحدات", {
        m: ALL for m in ["dashboard", "pmo", "crm", "selling", "buying", "inventory", "warehouses",
                          "reorder", "manufacturing", "assets", "hr", "accounting", "invoicing",
                          "taxes", "controls", "regulatory", "company-setup", "users", "audit", "settings"]
    }),
    ("Accountant", "محاسب", "المحاسبة والفواتير والضرائب", {
        "accounting": ALL, "invoicing": ALL, "taxes": ALL, "dashboard": VIEW, "audit": VIEW,
    }),
    ("Sales", "مبيعات", "العملاء والمبيعات والفواتير", {
        "crm": ALL, "selling": ALL, "invoicing": ALL, "inventory": VIEW, "dashboard": VIEW,
    }),
    ("Purchasing", "مشتريات", "المشتريات والمخزون وإعادة الطلب", {
        "buying": ALL, "inventory": ALL, "warehouses": ALL, "reorder": ALL, "dashboard": VIEW,
    }),
    ("HR Manager", "مدير موارد بشرية", "الموارد البشرية", {
        "hr": ALL, "dashboard": VIEW,
    }),
    ("Inventory", "أمين مخزون", "المخزون والمستودعات والأصول", {
        "inventory": ALL, "warehouses": ALL, "reorder": ALL, "assets": ALL, "dashboard": VIEW,
    }),
    ("Viewer", "مشاهد", "اطّلاع فقط على كل الوحدات", {
        m: VIEW for m in ["dashboard", "crm", "selling", "buying", "inventory", "accounting",
                          "invoicing", "hr", "assets", "reorder"]
    }),
]


class Command(BaseCommand):
    help = "Seed standard roles (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for name, name_ar, desc, perms in ROLES:
            _, created = Role.objects.update_or_create(
                name=name,
                defaults={"name_ar": name_ar, "description": desc, "permissions": perms, "is_system": True},
            )
            n += 1 if created else 0
        self.stdout.write(self.style.SUCCESS(f"Roles ensured: {Role.objects.count()} ({n} new)"))
