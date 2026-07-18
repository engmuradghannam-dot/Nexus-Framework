"""User-defined custom fields per module (tenant-scoped, no code required).

Three kinds of field, mirroring what a spreadsheet gives you:
  - plain input   (text/number/date/select/boolean/textarea) — the user types it
  - formula       — computed from other fields, like a cell with '=A*B'
  - lookup        — pulls a value from another table, like VLOOKUP

Values live in CustomFieldValue, keyed by (field, record) so any module's row
can carry them without altering that module's own table.
"""
from django.db import models


class CustomControl(models.Model):
    """A user-defined control: a named group of fields on a module, built with
    no code — like adding a whole section or sub-table to a form.

    Two layouts:
      - section  : one set of fields shown once (e.g. "Warranty details").
      - table    : a repeating set of rows (e.g. extra line items), each row
                   carrying the control's fields — like a mini spreadsheet.

    A control can also LINK to another module: a table control on the invoice
    can pull its rows from, say, a delivery-notes module, so the data is entered
    once and reused.
    """

    LAYOUTS = [("section", "Section"), ("table", "Repeating table")]

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    module = models.CharField(max_length=60, db_index=True)
    control_key = models.CharField(max_length=60)
    label = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120, blank=True)
    layout = models.CharField(max_length=10, choices=LAYOUTS, default="section")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Optional data link: this control's rows mirror rows of another module.
    linked_module = models.CharField(
        max_length=60, blank=True,
        help_text="If set, a table control reads its rows from this module "
        "instead of storing its own.",
    )
    linked_match_local = models.CharField(
        max_length=60, blank=True,
        help_text="Field on THIS record used to match linked rows.",
    )
    linked_match_source = models.CharField(
        max_length=60, blank=True,
        help_text="Field on the linked row that must equal the local value.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "custom_controls"
        ordering = ["module", "order", "id"]
        unique_together = ["tenant", "module", "control_key"]

    def __str__(self):
        return f"{self.module}.{self.control_key} ({self.layout})"

    @property
    def is_linked(self):
        return bool(self.linked_module and self.linked_match_local and self.linked_match_source)


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
    control = models.ForeignKey(
        "CustomControl", on_delete=models.CASCADE, null=True, blank=True,
        related_name="fields",
        help_text="The control (section/table) this field belongs to. Null means "
        "it sits directly on the module form, as before.",
    )
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
    row = models.ForeignKey(
        "CustomControlRow", on_delete=models.CASCADE, null=True, blank=True,
        related_name="values",
        help_text="Set when this value belongs to a row of a repeating control; "
        "null for a plain field or a section field.",
    )
    value = models.JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "custom_field_values"
        unique_together = ["field", "record_id", "row"]
        indexes = [models.Index(fields=["field", "record_id"])]

    def __str__(self):
        return f"{self.field.field_key}[{self.record_id}] = {self.value}"


class CustomControlRow(models.Model):
    """One row of a repeating (table) control for one parent record.

    A section control needs no rows — its fields store straight into
    CustomFieldValue against the parent record. A table control has many rows,
    and each field value in a row is keyed to the row, not the parent, so a
    parent can carry an arbitrary number of them — like line items.
    """

    control = models.ForeignKey(
        CustomControl, on_delete=models.CASCADE, related_name="rows"
    )
    record_id = models.CharField(max_length=64, db_index=True)
    row_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "custom_control_rows"
        ordering = ["control", "record_id", "row_index"]
        indexes = [models.Index(fields=["control", "record_id"])]

    def __str__(self):
        return f"{self.control.control_key}[{self.record_id}] row {self.row_index}"
