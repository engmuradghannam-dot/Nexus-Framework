"""Units of measure, conversions, and item variants (tenant-scoped)."""
import itertools
from decimal import Decimal

from django.db import models


class UnitOfMeasure(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    code = models.CharField(max_length=20)
    name_ar = models.CharField(max_length=80)
    symbol = models.CharField(max_length=12, blank=True)
    category = models.CharField(max_length=40, blank=True)   # count/weight/length/volume
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "units_of_measure"
        ordering = ["category", "code"]

    def __str__(self):
        return self.code


class UOMConversion(models.Model):
    """1 <from_unit> = <factor> <to_unit>."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    from_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name="conversions_from")
    to_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name="conversions_to")
    factor = models.DecimalField(max_digits=16, decimal_places=6)

    class Meta:
        db_table = "uom_conversions"

    def __str__(self):
        return f"1 {self.from_unit.code} = {self.factor} {self.to_unit.code}"


class ItemVariant(models.Model):
    """A concrete variant of a template item (e.g. size/colour combination)."""
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    template_code = models.CharField(max_length=50, db_index=True)
    template_name = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=80)
    attributes = models.JSONField(default=dict)   # {"المقاس": "M", "اللون": "أحمر"}
    extra_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "item_variants"
        ordering = ["template_code", "sku"]

    def __str__(self):
        return self.sku


def convert_uom(amount, from_unit, to_unit):
    amount = Decimal(str(amount or 0))
    if from_unit.id == to_unit.id:
        return amount
    direct = UOMConversion.objects.filter(from_unit=from_unit, to_unit=to_unit).first()
    if direct:
        return (amount * direct.factor).quantize(Decimal("0.0001"))
    reverse = UOMConversion.objects.filter(from_unit=to_unit, to_unit=from_unit).first()
    if reverse and reverse.factor:
        return (amount / reverse.factor).quantize(Decimal("0.0001"))
    return None


def generate_variants(template_code, template_name, attributes, tenant=None):
    """attributes = {"المقاس": ["S","M"], "اللون": ["أحمر","أزرق"]} -> cartesian SKUs."""
    keys = list(attributes.keys())
    value_lists = [attributes[k] for k in keys]
    created = []
    for combo in itertools.product(*value_lists):
        attr = dict(zip(keys, combo))
        suffix = "-".join(str(v) for v in combo)
        sku = f"{template_code}-{suffix}"
        obj, _ = ItemVariant.objects.get_or_create(
            template_code=template_code, sku=sku,
            defaults={"template_name": template_name, "attributes": attr, "tenant": tenant})
        created.append(obj)
    return created
