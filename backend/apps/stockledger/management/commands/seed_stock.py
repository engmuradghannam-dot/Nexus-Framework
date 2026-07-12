"""Seed sample stock movements to demonstrate valuation (idempotent)."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.stockledger.models import StockMovement

# item -> [(type, qty, unit_cost)] in chronological order
DATA = {
    ("IT-1001", "لابتوب ديل"): [("in", 20, 3000), ("in", 15, 3200), ("out", 18, 0), ("in", 10, 3300), ("out", 5, 0)],
    ("IT-1002", "طابعة HP"): [("in", 30, 800), ("out", 12, 0), ("in", 20, 900), ("out", 8, 0)],
    ("IT-1003", "كرسي مكتب"): [("in", 50, 380), ("in", 40, 400), ("out", 60, 0), ("in", 30, 420)],
}


class Command(BaseCommand):
    help = "Seed sample stock movements (idempotent)."

    def handle(self, *args, **options):
        if StockMovement.objects.exists():
            self.stdout.write("Stock movements already present — skipping.")
            return
        n = 0
        for (code, name), moves in DATA.items():
            for i, (t, qty, cost) in enumerate(moves):
                StockMovement.objects.create(
                    item_code=code, item_name=name, warehouse="الرياض",
                    movement_type=t, quantity=qty, unit_cost=cost,
                    date=date.today() - timedelta(days=len(moves) - i),
                    reference="فاتورة شراء" if t == "in" else "صرف مخزون",
                )
                n += 1
        self.stdout.write(self.style.SUCCESS(f"Stock movements seeded: {n}"))
