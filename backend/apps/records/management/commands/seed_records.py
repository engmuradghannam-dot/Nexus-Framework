"""Seed sample module records so CRUD pages are populated (idempotent)."""
from django.core.management.base import BaseCommand

from apps.records.models import ModuleRecord

SAMPLES = {
    "inventory": [
        {"item_code": "IT-1001", "sku": "SKU-1001", "arabic_name": "لابتوب ديل", "english_name": "Dell Laptop", "category": "إلكترونيات", "unit": "قطعة", "cost": 3200, "selling_price": 4100, "min_stock": 5, "max_stock": 50, "warehouse": "الرياض"},
        {"item_code": "IT-1002", "sku": "SKU-1002", "arabic_name": "طابعة HP", "english_name": "HP Printer", "category": "إلكترونيات", "unit": "قطعة", "cost": 850, "selling_price": 1200, "min_stock": 3, "max_stock": 30, "warehouse": "جدة"},
        {"item_code": "IT-1003", "sku": "SKU-1003", "arabic_name": "كرسي مكتب", "english_name": "Office Chair", "category": "أثاث", "unit": "قطعة", "cost": 400, "selling_price": 650, "min_stock": 10, "max_stock": 100, "warehouse": "الدمام"},
    ],
    "crm": [
        {"customer_code": "C-2001", "customer_name": "شركة الأفق للتجارة", "type": "Company", "phone": "0551234567", "email": "info@alufuq.sa", "city": "الرياض", "country": "Saudi Arabia", "salesperson": "خالد", "credit_limit": 100000, "status": "Active"},
        {"customer_code": "C-2002", "customer_name": "مؤسسة النور", "type": "Company", "phone": "0559876543", "email": "sales@alnoor.sa", "city": "جدة", "country": "Saudi Arabia", "salesperson": "سارة", "credit_limit": 50000, "status": "Active"},
        {"customer_code": "C-2003", "customer_name": "أحمد الغامدي", "type": "Individual", "phone": "0567778888", "email": "ahmad@mail.com", "city": "الدمام", "country": "Saudi Arabia", "salesperson": "خالد", "credit_limit": 15000, "status": "Inactive"},
    ],
    "hr": [
        {"employee_no": "E-3001", "name": "محمد العتيبي", "department": "المالية", "position": "محاسب أول", "hire_date": "2022-03-01", "nationality": "سعودي", "manager": "عبدالله", "status": "Active"},
        {"employee_no": "E-3002", "name": "نورة القحطاني", "department": "الموارد البشرية", "position": "أخصائي توظيف", "hire_date": "2023-06-15", "nationality": "سعودي", "manager": "منى", "status": "Active"},
        {"employee_no": "E-3003", "name": "راج كومار", "department": "تقنية المعلومات", "position": "مطوّر", "hire_date": "2021-01-10", "nationality": "هندي", "manager": "سامي", "status": "Active"},
    ],
    "assets": [
        {"asset_code": "A-4001", "asset_name": "سيارة تويوتا كامري", "category": "مركبات", "purchase_date": "2023-01-20", "cost": 120000, "location": "الرياض", "custodian": "إدارة النقل", "status": "Active"},
        {"asset_code": "A-4002", "asset_name": "خادم Dell PowerEdge", "category": "أجهزة", "purchase_date": "2022-09-05", "cost": 45000, "location": "غرفة الخوادم", "custodian": "تقنية المعلومات", "status": "Active"},
    ],
    "warehouses": [
        {"warehouse_code": "WH-01", "warehouse_name": "مستودع الرياض الرئيسي", "branch": "الرياض", "manager": "فهد", "location": "المنطقة الصناعية الثانية", "capacity": 5000, "status": "Active"},
        {"warehouse_code": "WH-02", "warehouse_name": "مستودع جدة", "branch": "جدة", "manager": "ماجد", "location": "حي الصناعية", "capacity": 3000, "status": "Active"},
    ],
    "selling": [
        {"so_no": "SO-5001", "customer": "شركة الأفق للتجارة", "date": "2026-07-01", "currency": "SAR", "warehouse": "الرياض", "salesperson": "خالد", "status": "Approved", "total": 45000},
        {"so_no": "SO-5002", "customer": "مؤسسة النور", "date": "2026-07-05", "currency": "SAR", "warehouse": "جدة", "salesperson": "سارة", "status": "Draft", "total": 18500},
    ],
    "buying": [
        {"po_no": "PO-6001", "supplier": "Sample Supplier 1", "pr_no": "PR-01", "currency": "SAR", "payment_terms": "صافي 30", "delivery_date": "2026-07-20", "buyer": "عمر", "status": "Approved", "total": 32000},
        {"po_no": "PO-6002", "supplier": "Sample Supplier 2", "pr_no": "PR-02", "currency": "SAR", "payment_terms": "صافي 60", "delivery_date": "2026-07-25", "buyer": "عمر", "status": "Pending", "total": 12500},
    ],
}


class Command(BaseCommand):
    help = "Seed sample module records (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for module, rows in SAMPLES.items():
            for row in rows:
                key = list(row.values())[0]  # first field = natural code
                exists = any(
                    r.data.get(list(row.keys())[0]) == key
                    for r in ModuleRecord.objects.filter(module=module)
                )
                if not exists:
                    ModuleRecord.objects.create(module=module, data=row)
                    n += 1
        self.stdout.write(self.style.SUCCESS(f"Sample records seeded: {n} new records"))
