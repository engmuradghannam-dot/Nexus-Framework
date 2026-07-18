from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.tenants.mixins import TenantScopedMixin

from .engine import FormulaError, evaluate_formula, resolve_lookup
from .models import CustomControl, CustomControlRow, CustomField, CustomFieldValue
from .serializers import (
    CustomControlSerializer,
    CustomFieldSerializer,
    CustomFieldValueSerializer,
)


class CustomFieldViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = CustomField.objects.filter(is_active=True)
    serializer_class = CustomFieldSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module", "field_type"]
    pagination_class = None

    @action(detail=False, methods=["get"])
    def modules(self, request):
        """Distinct modules that have custom fields defined."""
        qs = self.filter_queryset(self.get_queryset())
        return Response(sorted(set(qs.values_list("module", flat=True))))

    @action(detail=False, methods=["get", "post"], url_path=r"records/(?P<module>[^/]+)/(?P<record_id>[^/]+)")
    def record_values(self, request, module=None, record_id=None):
        """Read or write all custom field values for one record.

        GET  returns every field for the module with this record's value, with
             formula and lookup fields COMPUTED from the stored ones.
        POST accepts {field_key: value, ...} and stores the input fields. It
             ignores computed fields — you don't store a formula's output, you
             derive it — so they can never drift from their inputs.
        """
        fields = list(
            CustomField.objects.filter(module=module, is_active=True).order_by("order", "id")
        )
        if request.method == "POST":
            incoming = request.data or {}
            stored = {}
            for field in fields:
                if field.is_computed:
                    continue  # never store a computed value
                if field.field_key in incoming:
                    CustomFieldValue.objects.update_or_create(
                        field=field, record_id=str(record_id),
                        defaults={"value": incoming[field.field_key]},
                    )
                    stored[field.field_key] = incoming[field.field_key]
            # fall through to return the freshly computed view

        # Gather stored (input) values for this record.
        stored_values = {
            v.field.field_key: v.value
            for v in CustomFieldValue.objects.filter(
                field__in=fields, record_id=str(record_id)
            ).select_related("field")
        }

        result = []
        for field in fields:
            entry = {
                "field_key": field.field_key,
                "label": field.label,
                "label_ar": field.label_ar,
                "field_type": field.field_type,
                "computed": field.is_computed,
            }
            if field.field_type == "formula":
                try:
                    entry["value"] = str(evaluate_formula(field.formula, stored_values))
                except FormulaError as exc:
                    entry["value"] = None
                    entry["error"] = str(exc)
            elif field.field_type == "lookup":
                val = resolve_lookup(field, stored_values)
                entry["value"] = str(val) if val is not None else None
            else:
                entry["value"] = stored_values.get(field.field_key)
            result.append(entry)

        return Response({"module": module, "record_id": record_id, "fields": result})


class CustomFieldValueViewSet(viewsets.ModelViewSet):
    """Direct access to individual stored values, for callers that want it.

    Computed fields are refused here too — their value is derived, not set.
    """

    queryset = CustomFieldValue.objects.select_related("field")
    serializer_class = CustomFieldValueSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["field", "record_id"]

    def _reject_if_computed(self, field):
        if field and field.is_computed:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"field": f"'{field.field_key}' is a {field.field_type} field; its "
                          f"value is computed, not stored."}
            )

    def perform_create(self, serializer):
        self._reject_if_computed(serializer.validated_data.get("field"))
        serializer.save()

    def perform_update(self, serializer):
        self._reject_if_computed(serializer.instance.field)
        serializer.save()


class CustomControlViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    """Define controls — named groups of fields (sections or repeating tables)
    — for any module, no code required."""

    queryset = CustomControl.objects.filter(is_active=True).prefetch_related("fields")
    serializer_class = CustomControlSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["module", "layout"]
    pagination_class = None

    def _compute_row(self, fields, stored):
        """A row's values with formula/lookup fields computed from the row's
        own stored inputs."""
        out = {}
        for f in fields:
            if f.field_type == "formula":
                try:
                    out[f.field_key] = str(evaluate_formula(f.formula, stored))
                except FormulaError as exc:
                    out[f.field_key] = None
            elif f.field_type == "lookup":
                val = resolve_lookup(f, stored)
                out[f.field_key] = str(val) if val is not None else None
            else:
                out[f.field_key] = stored.get(f.field_key)
        return out

    @action(detail=True, methods=["get", "post"],
            url_path=r"records/(?P<record_id>[^/]+)")
    def rows(self, request, pk=None, record_id=None):
        """Read or replace the rows of a repeating control for one record.

        GET  returns each row with formula/lookup fields computed.
        POST accepts {"rows": [{field_key: value, ...}, ...]} and replaces the
             control's rows for this record atomically. Computed fields in the
             payload are ignored — they're derived, never stored.
        """
        from django.db import transaction

        control = self.get_object()
        fields = list(control.fields.filter(is_active=True).order_by("order", "id"))

        if control.layout != "table":
            return Response(
                {"detail": "Rows apply only to a repeating (table) control."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            incoming = request.data.get("rows", [])
            with transaction.atomic():
                CustomControlRow.objects.filter(
                    control=control, record_id=str(record_id)
                ).delete()  # cascades to that row's values
                for idx, row_data in enumerate(incoming):
                    row = CustomControlRow.objects.create(
                        control=control, record_id=str(record_id), row_index=idx,
                    )
                    for f in fields:
                        if f.is_computed:
                            continue
                        if f.field_key in row_data:
                            CustomFieldValue.objects.create(
                                field=f, record_id=str(record_id), row=row,
                                value=row_data[f.field_key],
                            )

        rows_out = []
        for row in CustomControlRow.objects.filter(
            control=control, record_id=str(record_id)
        ).order_by("row_index").prefetch_related("values__field"):
            stored = {v.field.field_key: v.value for v in row.values.all()}
            rows_out.append({"row_index": row.row_index, **self._compute_row(fields, stored)})

        return Response({
            "control": control.control_key,
            "layout": control.layout,
            "record_id": record_id,
            "fields": [{"field_key": f.field_key, "label": f.label,
                        "label_ar": f.label_ar, "field_type": f.field_type,
                        "computed": f.is_computed} for f in fields],
            "rows": rows_out,
        })
