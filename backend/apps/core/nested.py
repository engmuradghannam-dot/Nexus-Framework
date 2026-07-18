"""Writable nested line items for documents.

Invoices, Sales Orders and Purchase Orders are all header + lines. Until now the
lines could only be written through their own endpoints, one HTTP request each,
after the header already existed — so creating a three-line invoice took four
round trips and left a header with no lines behind if any of them failed. The
order serializers didn't expose their lines at all, in either direction.

This mixin lets a document be created or updated with its lines in a single
request, atomically, while leaving the standalone line endpoints working for
callers that already use them.
"""
from django.db import transaction
from rest_framework import serializers


class NestedLineItemsMixin:
    """Adds create/update handling for one writable nested line collection.

    Configure:
      ``lines_field``  — the serializer field name (e.g. "items", "line_items")
      ``lines_model``  — the child model class
      ``lines_parent`` — the FK attribute on the child pointing at the parent
      ``editable_statuses`` — parent statuses whose lines may be replaced

    Semantics on update: lines are replaced only when the caller actually sends
    the field. Omitting it leaves the existing lines alone, so a PATCH that only
    changes the header (a status transition, say) doesn't silently wipe them —
    which is the failure mode of naively replacing on every write.
    """

    lines_field = "items"
    lines_model = None
    lines_parent = None
    editable_statuses = ("Draft",)

    def _pop_lines(self, validated_data):
        return validated_data.pop(self.lines_field, serializers.empty)

    def _write_lines(self, parent, lines):
        for line in lines:
            self.lines_model.objects.create(**{self.lines_parent: parent}, **line)
        recalc = getattr(parent, "recalculate_totals", None)
        if recalc:
            recalc()

    @transaction.atomic
    def create(self, validated_data):
        lines = self._pop_lines(validated_data)
        instance = super().create(validated_data)
        if lines is not serializers.empty:
            self._write_lines(instance, lines)
            instance.refresh_from_db()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = self._pop_lines(validated_data)
        if lines is not serializers.empty:
            status = getattr(instance, "status", None)
            if status is not None and status not in self.editable_statuses:
                raise serializers.ValidationError({
                    self.lines_field: f"Cannot change lines on a document in status "
                                      f"'{status}'."
                })
            instance.lines_to_replace = True
        instance = super().update(instance, validated_data)
        if lines is not serializers.empty:
            getattr(instance, self.lines_field).all().delete()
            self._write_lines(instance, lines)
            instance.refresh_from_db()
        return instance
