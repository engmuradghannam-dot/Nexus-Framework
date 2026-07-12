"""Seed sample trade documents (idempotent)."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.trade.models import TradeDoc

SAMPLES = [
    ("quotation", "QT-0001", "شركة الأفق للتجارة", "IT-1001", "لابتوب ديل", 5, 4100),
    ("quotation", "QT-0002", "مؤسسة النور", "IT-1003", "كرسي مكتب", 20, 650),
    ("receipt", "GRN-0001", "المورّد المتحد", "IT-1001", "لابتوب ديل", 15, 3200),
    ("delivery", "DN-0001", "شركة الأفق للتجارة", "IT-1002", "طابعة HP", 4, 1200),
]


class Command(BaseCommand):
    help = "Seed sample trade documents (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for i, (t, num, party, code, name, qty, price) in enumerate(SAMPLES):
            if TradeDoc.objects.filter(number=num).exists():
                continue
            TradeDoc.objects.create(
                doc_type=t, number=num, party_name=party, item_code=code, item_name=name,
                quantity=qty, unit_price=price, warehouse="الرياض",
                date=date.today() - timedelta(days=i),
            )
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Trade documents seeded: {n} new"))
