"""Seed ZATCA-aligned Saudi VAT tax templates (idempotent)."""
from django.core.management.base import BaseCommand

from apps.taxes.models import TaxTemplate

TEMPLATES = [
    ("Standard Rated 15%", "الأساسي 15%", 15, "S", "ضريبة القيمة المضافة القياسية", True),
    ("Zero Rated 0%", "معدّل صفري 0%", 0, "Z", "صادرات وسلع خاضعة لمعدل صفري", False),
    ("Exempt", "معفى", 0, "E", "خدمات مالية وعقارية معفاة", False),
    ("Out of Scope", "خارج النطاق", 0, "O", "غير خاضع للضريبة", False),
]


class Command(BaseCommand):
    help = "Seed ZATCA VAT tax templates (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for name, name_ar, rate, cat, desc, default in TEMPLATES:
            _, created = TaxTemplate.objects.update_or_create(
                name=name,
                defaults={"name_ar": name_ar, "rate": rate, "zatca_category": cat,
                          "description": desc, "is_default": default},
            )
            n += 1 if created else 0
        self.stdout.write(self.style.SUCCESS(f"Tax templates ensured: {TaxTemplate.objects.count()} ({n} new)"))
