"""Depreciable assets + depreciation schedule (straight-line / declining)."""
from decimal import Decimal

from django.db import models


class DepreciableAsset(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    METHODS = [("straight_line", "Straight Line"), ("declining", "Declining Balance")]

    name = models.CharField(max_length=200)
    asset_code = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=100, blank=True)
    cost = models.DecimalField(max_digits=16, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    useful_life_years = models.PositiveSmallIntegerField(default=5)
    purchase_date = models.DateField()
    method = models.CharField(max_length=15, choices=METHODS, default="straight_line")

    class Meta:
        db_table = "depreciable_assets"
        ordering = ["-purchase_date", "name"]

    def __str__(self):
        return f"{self.name} ({self.cost})"

    def schedule(self):
        cost = Decimal(self.cost or 0)
        salvage = Decimal(self.salvage_value or 0)
        life = int(self.useful_life_years or 1)
        rows = []
        book = cost
        year0 = self.purchase_date.year if self.purchase_date else 0
        if self.method == "declining":
            rate = Decimal(2) / Decimal(life)  # double-declining
            for i in range(life):
                dep = (book * rate).quantize(Decimal("0.01"))
                if book - dep < salvage:
                    dep = (book - salvage).quantize(Decimal("0.01"))
                book = (book - dep).quantize(Decimal("0.01"))
                rows.append({"year": year0 + i, "depreciation": float(dep),
                             "accumulated": float(cost - book), "book_value": float(book)})
        else:
            annual = ((cost - salvage) / life).quantize(Decimal("0.01"))
            for i in range(life):
                dep = annual
                if book - dep < salvage:
                    dep = (book - salvage).quantize(Decimal("0.01"))
                book = (book - dep).quantize(Decimal("0.01"))
                rows.append({"year": year0 + i, "depreciation": float(dep),
                             "accumulated": float(cost - book), "book_value": float(book)})
        return rows
