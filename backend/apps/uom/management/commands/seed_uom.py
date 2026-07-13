from django.core.management.base import BaseCommand

from apps.uom.models import UnitOfMeasure, UOMConversion

UNITS = [
    ("PCS", "قطعة", "قطعة", "count"), ("BOX", "صندوق", "صندوق", "count"),
    ("DOZ", "دزينة", "دزينة", "count"), ("KG", "كيلوغرام", "كجم", "weight"),
    ("G", "غرام", "غم", "weight"), ("TON", "طن", "طن", "weight"),
    ("M", "متر", "م", "length"), ("CM", "سنتيمتر", "سم", "length"),
    ("L", "لتر", "ل", "volume"),
]
CONV = [("BOX", "PCS", 24), ("DOZ", "PCS", 12), ("KG", "G", 1000), ("TON", "KG", 1000), ("M", "CM", 100)]


class Command(BaseCommand):
    help = "Seed common units of measure + conversions (idempotent)."

    def handle(self, *args, **options):
        for code, name, sym, cat in UNITS:
            UnitOfMeasure.objects.get_or_create(code=code, defaults={"name_ar": name, "symbol": sym, "category": cat})
        for f, t, factor in CONV:
            fu = UnitOfMeasure.objects.filter(code=f).first()
            tu = UnitOfMeasure.objects.filter(code=t).first()
            if fu and tu and not UOMConversion.objects.filter(from_unit=fu, to_unit=tu).exists():
                UOMConversion.objects.create(from_unit=fu, to_unit=tu, factor=factor)
        self.stdout.write(self.style.SUCCESS(f"UOM ensured: {UnitOfMeasure.objects.count()} units, {UOMConversion.objects.count()} conversions"))
