"""Multi-currency: currencies + exchange rates against a base currency (SAR)."""
from decimal import Decimal

from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)      # ISO 4217, e.g. USD
    name = models.CharField(max_length=80)
    name_ar = models.CharField(max_length=80, blank=True)
    symbol = models.CharField(max_length=8, blank=True)
    is_base = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # 1 unit of this currency = `rate` units of the base currency (SAR)
    rate_to_base = models.DecimalField(max_digits=14, decimal_places=6, default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "currencies"
        ordering = ["-is_base", "code"]

    def __str__(self):
        return f"{self.code} ({self.rate_to_base})"


class ExchangeRate(models.Model):
    """Historical exchange-rate snapshots (audit of rate changes)."""
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="history")
    rate_to_base = models.DecimalField(max_digits=14, decimal_places=6)
    date = models.DateField()

    class Meta:
        db_table = "exchange_rates"
        ordering = ["-date"]


def convert(amount, from_code, to_code):
    """Convert amount from one currency to another via the base currency."""
    amount = Decimal(str(amount or 0))
    try:
        f = Currency.objects.get(code=from_code)
        t = Currency.objects.get(code=to_code)
    except Currency.DoesNotExist:
        return None
    base = amount * Decimal(f.rate_to_base)          # to base (SAR)
    if Decimal(t.rate_to_base) == 0:
        return None
    return (base / Decimal(t.rate_to_base)).quantize(Decimal("0.01"))
