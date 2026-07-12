from django.core.management.base import BaseCommand

from apps.currencies.models import Currency

# code, name, name_ar, symbol, is_base, rate_to_base (1 unit = X SAR)
DATA = [
    ("SAR", "Saudi Riyal", "ريال سعودي", "ر.س", True, 1),
    ("USD", "US Dollar", "دولار أمريكي", "$", False, 3.75),
    ("EUR", "Euro", "يورو", "€", False, 4.05),
    ("AED", "UAE Dirham", "درهم إماراتي", "د.إ", False, 1.02),
    ("KWD", "Kuwaiti Dinar", "دينار كويتي", "د.ك", False, 12.20),
    ("QAR", "Qatari Riyal", "ريال قطري", "ر.ق", False, 1.03),
    ("BHD", "Bahraini Dinar", "دينار بحريني", "د.ب", False, 9.95),
    ("OMR", "Omani Rial", "ريال عماني", "ر.ع", False, 9.74),
    ("GBP", "British Pound", "جنيه إسترليني", "£", False, 4.75),
    ("EGP", "Egyptian Pound", "جنيه مصري", "ج.م", False, 0.078),
]


class Command(BaseCommand):
    help = "Seed currencies with indicative rates (idempotent)."

    def handle(self, *args, **options):
        for code, name, name_ar, sym, base, rate in DATA:
            Currency.objects.update_or_create(
                code=code,
                defaults={"name": name, "name_ar": name_ar, "symbol": sym,
                          "is_base": base, "rate_to_base": rate})
        self.stdout.write(self.style.SUCCESS(f"Currencies ensured: {Currency.objects.count()}"))
