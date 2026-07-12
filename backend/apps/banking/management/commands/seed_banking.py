from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.banking.models import BankAccount, BankTransaction


class Command(BaseCommand):
    help = "Seed a sample bank account with transactions (idempotent)."

    def handle(self, *args, **options):
        acc, _ = BankAccount.objects.get_or_create(
            name="الحساب الجاري - الراجحي",
            defaults={"bank_name": "مصرف الراجحي", "iban": "SA0380000000608010167519", "opening_balance": 500000},
        )
        if acc.transactions.exists():
            self.stdout.write("Bank transactions already present — skipping.")
            return
        rows = [
            ("تحصيل فاتورة SINV-0001", 115000, "in", True),
            ("سداد مورّد PINV-0001", 69000, "out", True),
            ("رسوم بنكية", 250, "out", False),
            ("تحصيل نقدي", 40000, "in", False),
            ("راتب الموظفين", 85000, "out", True),
        ]
        for i, (desc, amt, dirn, rec) in enumerate(rows):
            BankTransaction.objects.create(
                account=acc, date=date.today() - timedelta(days=i * 2),
                description=desc, amount=amt, direction=dirn, reconciled=rec,
            )
        self.stdout.write(self.style.SUCCESS("Bank account + transactions seeded"))
