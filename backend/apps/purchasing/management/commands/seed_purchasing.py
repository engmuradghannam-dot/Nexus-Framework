from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.purchasing.models import PurchaseDoc

SAMPLES = [
    ("rfq", "RFQ-0001", "المورّد المتحد", "IT-1001", "لابتوب ديل", 10, 3100),
    ("rfq", "RFQ-0002", "شركة الإمداد", "IT-1002", "طابعة HP", 15, 780),
    ("po", "PO-0001", "المورّد المتحد", "IT-1003", "كرسي مكتب", 40, 390),
]


class Command(BaseCommand):
    help = "Seed sample purchase documents (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for i, (t, num, sup, code, name, qty, price) in enumerate(SAMPLES):
            if PurchaseDoc.objects.filter(number=num).exists():
                continue
            PurchaseDoc.objects.create(doc_type=t, number=num, supplier_name=sup, item_code=code,
                item_name=name, quantity=qty, unit_price=price, warehouse="الرياض",
                date=date.today() - timedelta(days=i))
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Purchase documents seeded: {n} new"))
