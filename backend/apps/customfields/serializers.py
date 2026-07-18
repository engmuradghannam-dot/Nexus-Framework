from rest_framework import serializers

from .engine import FormulaError, evaluate_formula, referenced_keys
from .models import CustomControl, CustomControlRow, CustomField, CustomFieldValue


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = [
            "id", "module", "field_key", "label", "label_ar", "field_type",
            "options", "required", "order", "is_active", "control",
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


class CustomControlSerializer(serializers.ModelSerializer):
    fields = CustomFieldSerializer(many=True, read_only=True)

    class Meta:
        model = CustomControl
        fields = [
            "id", "module", "control_key", "label", "label_ar", "layout",
            "order", "is_active", "linked_module", "linked_match_local",
            "linked_match_source", "is_linked", "fields",
        ]
        read_only_fields = ["is_linked", "fields"]

    def validate(self, data):
        layout = data.get("layout", getattr(self.instance, "layout", "section"))
        linked = data.get("linked_module", getattr(self.instance, "linked_module", ""))
        if linked and layout != "table":
            raise serializers.ValidationError(
                {"linked_module": "Only a repeating (table) control can link to "
                                  "another module."}
            )
        if linked:
            for req in ("linked_match_local", "linked_match_source"):
                if not data.get(req, getattr(self.instance, req, "")):
                    raise serializers.ValidationError(
                        {req: "A linked control needs this set."}
                    )
        return data
