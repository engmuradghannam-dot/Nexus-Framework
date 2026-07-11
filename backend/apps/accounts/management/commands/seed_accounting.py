"""Seed a standard chart of accounts + balanced journal entries (idempotent)."""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed chart of accounts and sample journal entries (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.accounts.models import Account, JournalEntry
        from apps.core.models import Company

        company = Company.objects.order_by("id").first()
        if company is None:
            company = Company.objects.create(name="Nexus Demo Company")

        if Account.objects.filter(company=company).exists():
            self.stdout.write("Chart of accounts already present — skipping.")
            return

        # (number, name, root_type, is_group, parent_number)
        chart = [
            ("1000", "الأصول / Assets", "Asset", True, None),
            ("1100", "النقدية / Cash", "Asset", False, "1000"),
            ("1200", "البنك / Bank", "Asset", False, "1000"),
            ("1300", "المدينون / Accounts Receivable", "Asset", False, "1000"),
            ("1400", "المخزون / Inventory", "Asset", False, "1000"),
            ("1500", "الأصول الثابتة / Fixed Assets", "Asset", False, "1000"),
            ("2000", "الخصوم / Liabilities", "Liability", True, None),
            ("2100", "الدائنون / Accounts Payable", "Liability", False, "2000"),
            ("2200", "ضريبة القيمة المضافة المستحقة / VAT Payable", "Liability", False, "2000"),
            ("2300", "القروض / Loans", "Liability", False, "2000"),
            ("3000", "حقوق الملكية / Equity", "Equity", True, None),
            ("3100", "رأس المال / Capital", "Equity", False, "3000"),
            ("3200", "الأرباح المحتجزة / Retained Earnings", "Equity", False, "3000"),
            ("4000", "الإيرادات / Income", "Income", True, None),
            ("4100", "إيرادات المبيعات / Sales Revenue", "Income", False, "4000"),
            ("4200", "إيرادات الخدمات / Service Revenue", "Income", False, "4000"),
            ("5000", "المصروفات / Expenses", "Expense", True, None),
            ("5100", "تكلفة المبيعات / COGS", "Expense", False, "5000"),
            ("5200", "الرواتب / Salaries", "Expense", False, "5000"),
            ("5300", "الإيجار / Rent", "Expense", False, "5000"),
            ("5400", "المرافق / Utilities", "Expense", False, "5000"),
        ]
        acc = {}
        for number, name, root, is_group, parent in chart:
            acc[number] = Account.objects.create(
                company=company, account_number=number, account_name=name,
                account_type=root, root_type=root, is_group=is_group,
                parent_account=acc.get(parent) if parent else None,
                is_bank_account=(number == "1200"),
            )

        # (debit_number, credit_number, amount, description)
        entries = [
            ("1200", "3100", 500000, "ضخ رأس المال"),
            ("1400", "2100", 200000, "شراء مخزون بالآجل"),
            ("1300", "4100", 115000, "مبيعات بالآجل"),
            ("5100", "1400", 80000, "تكلفة البضاعة المباعة"),
            ("5200", "1200", 45000, "رواتب"),
            ("5300", "1200", 20000, "إيجار"),
            ("1200", "1300", 90000, "تحصيل من عميل"),
            ("2100", "1200", 100000, "سداد لمورّد"),
            ("5400", "1200", 8000, "فواتير مرافق"),
        ]
        for i, (d, c, amount, desc) in enumerate(entries, 1):
            amt = Decimal(amount)
            JournalEntry.objects.create(
                company=company,
                entry_number=f"JV-{i:04d}",
                posting_date=date.today() - timedelta(days=len(entries) - i),
                reference=desc,
                debit_account=acc[d],
                credit_account=acc[c],
                amount=amt,
                total_debit=amt,
                total_credit=amt,
            )
            acc[d].post(debit_amount=amt)
            acc[c].post(credit_amount=amt)

        self.stdout.write(
            self.style.SUCCESS(
                f"Accounting seeded: {len(chart)} accounts, {len(entries)} journal entries"
            )
        )
