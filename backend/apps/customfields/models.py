"""User-defined custom fields per module (tenant-scoped, no code required).

Three kinds of field, mirroring what a spreadsheet gives you:
  - plain input   (text/number/date/select/boolean/textarea) — the user types it
  - formula       — computed from other fields, like a cell with '=A*B'
  - lookup        — pulls a value from another table, like VLOOKUP

Values live in CustomFieldValue, keyed by (field, record) so any module's row
can carry them without altering that module's own table.
"""
from django.db import models


class CustomField(models.Model):
    TYPES = [
        ("text", "Text"), ("number", "Number"), ("date", "Date"),
        ("select", "Select"), ("boolean", "Boolean"), ("textarea", "Text Area"),
        ("formula", "Formula"), ("lookup", "Lookup"),
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    module = models.CharField(max_length=60, db_index=True)
    field_key = models.CharField(max_length=60)
    label = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120, blank=True)
    field_type = models.CharField(max_length=12, choices=TYPES, default="text")
    options = models.JSONField(default=list, blank=True)   # for select
    required = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # --- formula fields ---
    # An Excel-like expression referencing other fields by {field_key}, plus the
    # module's own numeric fields. Example: "{qty} * {unit_price} * 1.15".
    formula = models.TextField(
        blank=True,
        help_text="Expression using {field_key} references, e.g. '{qty} * {price}'. "
        "Only + - * / ( ) and numbers are allowed — no code.",
    )

    # --- lookup fields ---
    # Pull a value from another module's row, matched on a key. Like VLOOKUP:
    # 'find the row in <source_module> whose <source_match_field> equals this
    # record's <local_match_field>, and return its <source_return_field>'.
    lookup_module = models.CharField(max_length=60, blank=True)
    lookup_match_local = models.CharField(
        max_length=60, blank=True,
        help_text="Field on THIS record whose value we match on.",
    )
    lookup_match_source = models.CharField(
        max_length=60, blank=True,
        help_text="Field on the source row that must equal the local value.",
    )
    lookup_return = models.CharField(
        max_length=60, blank=True,
        help_text="Field on the matched source row to return.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "custom_fields"
        ordering = ["module", "order", "id"]
        unique_together = ["tenant", "module", "field_key"]

    def __str__(self):
        return f"{self.module}.{self.field_key}"

    @property
    def is_computed(self):
        """Computed fields hold no stored value — they're derived on read."""
        return self.field_type in ("formula", "lookup")


class CustomFieldValue(models.Model):
    """One custom field's value for one record in some module.

    record_id is the primary key of the row in the target module (an invoice id,
    an item id, ...). We don't FK it because the target differs by module; the
    module on the field plus record_id locates the row.
    """

    field = models.ForeignKey(
        CustomField, on_delete=models.CASCADE, related_name="values"
    )
    record_id = models.CharField(max_length=64, db_index=True)
    value = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "custom_field_values"
        unique_together = ["field", "record_id"]
        indexes = [models.Index(fields=["field", "record_id"])]

    def __str__(self):
        return f"{self.field.field_key}[{self.record_id}] = {self.value}"
