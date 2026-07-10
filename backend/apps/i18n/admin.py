from django.contrib import admin

from .models import Language, Translation, TranslationImportJob


class TranslationInline(admin.TabularInline):
    model = Translation
    extra = 0
    fields = ["key", "value", "context", "is_reviewed"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = [
        "code", "name", "name_local", "direction", "is_active", "is_default", "flag_emoji",
    ]
    list_filter = ["is_active", "direction"]
    search_fields = ["code", "name", "name_local"]
    inlines = [TranslationInline]


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ["key", "language", "value", "context", "is_reviewed", "updated_at"]
    list_filter = ["is_reviewed", "language", "context"]
    search_fields = ["key", "value"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TranslationImportJob)
class TranslationImportJobAdmin(admin.ModelAdmin):
    list_display = ["name", "language", "status", "total_rows", "processed_rows", "failed_rows", "created_at"]
    list_filter = ["status", "language"]
    readonly_fields = ["total_rows", "processed_rows", "failed_rows", "error_log", "created_at", "completed_at"]
