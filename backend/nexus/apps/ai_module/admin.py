from django.contrib import admin
from .models import AIModel, AIConversation, AIMessage, AIPromptTemplate

@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_id', 'is_active']
    list_filter = ['is_active', 'provider']

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'model', 'title', 'created_at']
    search_fields = ['title', 'user__username']

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'created_at']
    list_filter = ['role']

    def content_preview(self, obj):
        return obj.content[:50] + "..."
    content_preview.short_description = 'Content'

@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']
