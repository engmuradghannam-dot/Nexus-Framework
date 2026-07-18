"""Reject writes that reference another company's records.

CompanyScopedMixin scopes what a user can *read*. Nothing scoped what they could
*reference*: a DRF PrimaryKeyRelatedField resolves against the model's default
manager, so a user of company A could POST a sales order naming company B's
customer and B's items. They never needed to see the record — primary keys are
sequential integers.

Reading was fail-closed while writing was wide open. This closes the write side.
"""
from rest_framework import serializers

# How to reach the owning company from a model that doesn't hold `company`
# itself. Keyed by model label, valued by the attribute chain to follow.
COMPANY_PATHS = {
    "core.Warehouse": ("branch", "company_id"),
    "core.BinLocation": ("warehouse", "branch", "company_id"),
    "core.Branch": ("company_id",),
}


def company_id_of(obj):
    """The company that owns `obj`, or None if it isn't company-scoped."""
    if obj is None:
        return None
    label = obj._meta.label
    if label in COMPANY_PATHS:
        current = obj
        for step in COMPANY_PATHS[label][:-1]:
            current = getattr(current, step, None)
            if current is None:
                return None
        return getattr(current, COMPANY_PATHS[label][-1], None)
    return getattr(obj, "company_id", None)


def is_company_scoped(model):
    if model._meta.label in COMPANY_PATHS:
        return True
    return any(f.name == "company" for f in model._meta.get_fields())


class CompanyConsistencyMixin:
    """Validate that every company-scoped FK in the payload shares one company.

    Configure ``owner_field`` when the record reaches its company through a
    parent instead of holding one directly (e.g. a line item via its order).

    Fields listed in ``consistency_exempt`` are skipped — use it only for
    genuinely cross-company references, and say why.
    """

    owner_field = None
    consistency_exempt = ()

    def _own_company_id(self, data):
        if self.owner_field:
            parent = data.get(self.owner_field) or getattr(
                self.instance, self.owner_field, None
            )
            # When nested, the parent doesn't exist yet and the line cannot
            # reach a company. That case is covered by the parent serializer,
            # which checks its own line payloads (see validate()).
            return company_id_of(parent)
        company = data.get("company") or getattr(self.instance, "company", None)
        return getattr(company, "pk", None)

    def validate(self, data):
        data = super().validate(data)
        own = self._own_company_id(data)
        if own is None:
            # Nothing to compare against — either the company is being resolved
            # later by the viewset, or this record genuinely has no owner yet.
            return data

        errors = {}
        for name, value in data.items():
            if name in ("company", self.owner_field) or name in self.consistency_exempt:
                continue
            if value is None:
                continue
            # Nested line collections arrive as a list of dicts. DRF validates
            # them during the parent's to_internal_value — i.e. BEFORE this
            # method runs — and at that point a line has no parent to reach a
            # company through, so it cannot check itself. The parent has to.
            if isinstance(value, list):
                for index, row in enumerate(value):
                    if not isinstance(row, dict):
                        continue
                    for field, ref in row.items():
                        problem = self._mismatch(ref, own)
                        if problem:
                            errors[f"{name}[{index}].{field}"] = problem
                continue
            problem = self._mismatch(value, own)
            if problem:
                errors[name] = problem
        if errors:
            raise serializers.ValidationError(errors)
        return data

    @staticmethod
    def _mismatch(value, own):
        if value is None or not hasattr(value, "_meta"):
            return None
        if not is_company_scoped(value._meta.model):
            return None
        other = company_id_of(value)
        if other is not None and other != own:
            return (
                f"'{value}' belongs to a different company and cannot be "
                f"referenced here."
            )
        return None
