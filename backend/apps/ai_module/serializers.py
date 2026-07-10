from rest_framework import serializers

from .models import AIModel, Insight, Prediction


class PredictionSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="model.name", read_only=True)

    class Meta:
        model = Prediction
        fields = [
            "id",
            "model",
            "model_name",
            "input_data",
            "output_data",
            "confidence",
            "latency_ms",
            "created_at",
        ]


class InsightSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="source_model.name", read_only=True)
    project_name = serializers.CharField(source="related_project.name", read_only=True)

    class Meta:
        model = Insight
        fields = [
            "id",
            "title",
            "description",
            "severity",
            "source_model",
            "model_name",
            "related_project",
            "project_name",
            "is_read",
            "created_at",
        ]


class AIModelSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    prediction_count = serializers.IntegerField(
        source="predictions.count", read_only=True
    )
    insight_count = serializers.IntegerField(source="insights.count", read_only=True)

    class Meta:
        model = AIModel
        fields = [
            "id",
            "name",
            "version",
            "model_type",
            "status",
            "description",
            "accuracy",
            "f1_score",
            "training_data_size",
            "last_trained",
            "deployed_at",
            "owner",
            "owner_name",
            "prediction_count",
            "insight_count",
            "is_active",
            "created_at",
        ]
