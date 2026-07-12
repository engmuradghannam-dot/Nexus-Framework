from datetime import date

from django.core.management.base import BaseCommand

from apps.depreciation.models import DepreciableAsset

SAMPLES = [
    ("سيارة نقل", "AST-CAR-1", "مركبات", 120000, 20000, 5, "straight_line"),
    ("أجهزة حاسب", "AST-IT-1", "إلكترونيات", 80000, 5000, 4, "declining"),
    ("أثاث مكتبي", "AST-FUR-1", "أثاث", 50000, 5000, 10, "straight_line"),
]


class Command(BaseCommand):
    help = "Seed sample depreciable assets (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for name, code, cat, cost, salv, life, method in SAMPLES:
            _, created = DepreciableAsset.objects.get_or_create(
                asset_code=code,
                defaults={"name": name, "category": cat, "cost": cost, "salvage_value": salv,
                          "useful_life_years": life, "method": method, "purchase_date": date(2024, 1, 1)},
            )
            n += 1 if created else 0
        self.stdout.write(self.style.SUCCESS(f"Depreciable assets ensured: {DepreciableAsset.objects.count()} ({n} new)"))
