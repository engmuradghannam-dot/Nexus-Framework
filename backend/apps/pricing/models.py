"""Pricing rules / promotions (tenant-scoped)."""
from decimal import Decimal

from django.db import models


class PricingRule(models.Model):
    SCOPES = [("all", "All Items"), ("item", "Specific Item"), ("category", "Category")]
    DISCOUNTS = [("percent", "Percentage"), ("fixed_amount", "Fixed Amount Off"), ("fixed_price", "Fixed Price")]

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    name = models.CharField(max_length=150)
    name_ar = models.CharField(max_length=150, blank=True)
    scope = models.CharField(max_length=10, choices=SCOPES, default="all")
    target = models.CharField(max_length=120, blank=True)   # item_code or category
    min_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    discount_type = models.CharField(max_length=12, choices=DISCOUNTS, default="percent")
    discount_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pricing_rules"
        ordering = ["-priority", "name"]

    def __str__(self):
        return self.name

    def matches(self, item_code, category, quantity, on_date):
        if not self.is_active:
            return False
        if Decimal(str(quantity or 0)) < Decimal(self.min_quantity or 0):
            return False
        if self.valid_from and on_date and on_date < self.valid_from:
            return False
        if self.valid_to and on_date and on_date > self.valid_to:
            return False
        if self.scope == "item" and self.target and item_code != self.target:
            return False
        if self.scope == "category" and self.target and category != self.target:
            return False
        return True

    def apply(self, base_price):
        base = Decimal(str(base_price or 0))
        v = Decimal(self.discount_value or 0)
        if self.discount_type == "percent":
            final = base * (Decimal(1) - v / Decimal(100))
        elif self.discount_type == "fixed_amount":
            final = base - v
        else:  # fixed_price
            final = v
        return max(final, Decimal(0)).quantize(Decimal("0.01"))


def best_price(rules, item_code, category, quantity, base_price, on_date):
    """Pick the highest-priority matching rule and return (final_price, rule)."""
    matching = [r for r in rules if r.matches(item_code, category, quantity, on_date)]
    if not matching:
        return Decimal(str(base_price or 0)).quantize(Decimal("0.01")), None
    rule = sorted(matching, key=lambda r: (r.priority, r.discount_value), reverse=True)[0]
    return rule.apply(base_price), rule
