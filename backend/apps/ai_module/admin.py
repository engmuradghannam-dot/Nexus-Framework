from apps.core.admin_site import admin_site
from .models import AIModel, Prediction, Insight


@admin.register(AIModel, site=admin_site)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'model_type', 'status', 'accuracy',
                    'owner', 'last_trained', 'is_active']
    list_filter = ['model_type', 'status', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Prediction, site=admin_site)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['model', 'confidence', 'latency_ms', 'created_at']
    list_filter = ['model']


@admin.register(Insight, site=admin_site)
class InsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'severity', 'source_model', 'is_read', 'created_at']
    list_filter = ['severity', 'is_read']
