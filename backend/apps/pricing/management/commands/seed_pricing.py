from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.pricing.models import PricingRule


class Command(BaseCommand):
    help = "Seed sample pricing rules (idempotent)."

    def handle(self, *args, **options):
        data = [
            ("Bulk 10% off", "خصم الجملة 10%", "all", "", 10, "percent", 10, 5),
            ("Electronics promo", "عرض الإلكترونيات", "category", "إلكترونيات", 1, "percent", 15, 8),
            ("Laptop fixed price", "سعر ثابت للابتوب", "item", "IT-1001", 1, "fixed_price", 3900, 10),
        ]
        for name, name_ar, scope, target, minq, dtype, dval, prio in data:
            PricingRule.objects.get_or_create(
                name=name,
                defaults={"name_ar": name_ar, "scope": scope, "target": target,
                          "min_quantity": minq, "discount_type": dtype, "discount_value": dval,
                          "priority": prio, "valid_to": date.today() + timedelta(days=90)})
        self.stdout.write(self.style.SUCCESS(f"Pricing rules ensured: {PricingRule.objects.count()}"))
