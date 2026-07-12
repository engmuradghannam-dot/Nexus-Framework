"""Seed sample invoices (idempotent)."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.invoicing.models import Invoice

SAMPLES = [
    ("sales", "SINV-0001", "شركة الأفق للتجارة", 100000),
    ("sales", "SINV-0002", "مؤسسة النور", 40000),
    ("purchase", "PINV-0001", "المورّد المتحد", 60000),
]


class Command(BaseCommand):
    help = "Seed sample invoices (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for i, (itype, num, party, sub) in enumerate(SAMPLES):
            if Invoice.objects.filter(invoice_number=num).exists():
                continue
            Invoice.objects.create(
                invoice_type=itype, invoice_number=num, party_name=party,
                invoice_date=date.today() - timedelta(days=i * 3), subtotal=sub,
            )
            n += 1
        self.stdout.write(self.style.SUCCESS(f"Invoices seeded: {n} new"))
