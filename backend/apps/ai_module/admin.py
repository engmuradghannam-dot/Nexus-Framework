from django.contrib import admin
from .models import AIModel, Prediction, Insight


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'model_type', 'status', 'accuracy',
                    'owner', 'last_trained', 'is_active']
    list_filter = ['model_type', 'status', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['model', 'confidence', 'latency_ms', 'created_at']
    list_filter = ['model']


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'source_model', 'is_read', 'created_at']
    list_filter = ['severity', 'is_read']
