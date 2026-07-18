from rest_framework import serializers

from .engine import FormulaError, evaluate_formula, referenced_keys
from .models import CustomField, CustomFieldValue


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = [
            "id", "module", "field_key", "label", "label_ar", "field_type",
            "options", "required", "order", "is_active",
            "formula", "lookup_module", "lookup_match_local",
            "lookup_match_source", "lookup_return", "is_computed",
        ]
        read_only_fields = ["is_computed"]

    def validate(self, data):
        ftype = data.get("field_type", getattr(self.instance, "field_type", "text"))

        if ftype == "formula":
            formula = data.get("formula", getattr(self.instance, "formula", ""))
            if not formula or not formula.strip():
                raise serializers.ValidationError(
                    {"formula": "A formula field needs a formula."}
                )
            # Prove it parses safely now, with dummy values, so a broken or
            # unsafe formula can never be saved and blow up at read time.
            dummy = {k: 1 for k in referenced_keys(formula)}
            try:
                evaluate_formula(formula, dummy)
            except FormulaError as exc:
                raise serializers.ValidationError({"formula": str(exc)})

        if ftype == "lookup":
            for req in ("lookup_module", "lookup_match_local",
                        "lookup_match_source", "lookup_return"):
                val = data.get(req, getattr(self.instance, req, ""))
                if not val:
                    raise serializers.ValidationError(
                        {req: "A lookup field needs this set."}
                    )
        return data


class CustomFieldValueSerializer(serializers.ModelSerializer):
    field_key = serializers.CharField(source="field.field_key", read_only=True)

    class Meta:
        model = CustomFieldValue
        fields = ["id", "field", "field_key", "record_id", "value", "updated_at"]
        read_only_fields = ["updated_at"]
