from rest_framework import serializers

from .models import (
    AIAgent,
    CompanySetup,
    FormControl,
    Industry,
    IndustryControl,
    MasterEntity,
    SectorControl,
)


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ["id", "code", "name", "category", "description"]


class IndustryControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryControl
        fields = [
            "id",
            "industry",
            "module",
            "control_id",
            "control_name",
            "sub_control",
            "description",
            "required",
            "ai_agent",
            "database_entity",
            "kpi",
            "compliance",
        ]


class AIAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAgent
        fields = ["id", "industry", "name", "responsibility", "database_entity"]


class MasterEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterEntity
        fields = ["id", "name", "entity_type", "usage"]


class FormControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormControl
        fields = [
            "id",
            "seq",
            "form_name",
            "input_name",
            "input_type",
            "status",
            "priority",
        ]


class SectorControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectorControl
        fields = ["id", "sector", "entity", "description", "fields", "module", "icon", "is_core", "order"]


class CompanySetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySetup
        fields = "__all__"
        read_only_fields = ["created_by"]
