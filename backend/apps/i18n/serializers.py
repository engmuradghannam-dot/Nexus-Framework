from rest_framework import serializers

from .models import Language, Translation, TranslationImportJob


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id", "code", "name", "name_local", "direction", "is_active",
            "is_default", "flag_emoji", "decimal_separator", "thousands_separator",
            "date_format", "time_format", "first_day_of_week", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LanguageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "code", "name", "name_local", "flag_emoji", "is_active", "is_default", "direction", "date_format", "decimal_separator"]


class TranslationSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source="language.code", read_only=True)

    class Meta:
        model = Translation
        fields = [
            "id", "language", "language_code", "key", "value", "context",
            "is_reviewed", "reviewed_by", "reviewed_at", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "language_code", "created_at", "updated_at"]


class TranslationBulkCreateSerializer(serializers.Serializer):
    language_code = serializers.CharField(max_length=10)
    translations = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )

    def validate(self, attrs):
        from django.shortcuts import get_object_or_404
        from .models import Language
        attrs["language"] = get_object_or_404(Language, code=attrs["language_code"])
        return attrs


class TranslationImportJobSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source="language.code", read_only=True)

    class Meta:
        model = TranslationImportJob
        fields = [
            "id", "name", "file", "language", "language_code", "status",
            "total_rows", "processed_rows", "failed_rows", "error_log",
            "created_by", "created_at", "completed_at",
        ]
        read_only_fields = ["id", "status", "total_rows", "processed_rows", "failed_rows", "error_log", "created_at", "completed_at"]


class TranslationSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)
    context = serializers.CharField(required=False, allow_blank=True)
