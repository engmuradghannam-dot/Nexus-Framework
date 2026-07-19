from django.contrib import admin

from .models import ChangeHeader, ChangeItem


class ChangeItemInline(admin.TabularInline):
    model = ChangeItem
    extra = 0


@admin.register(ChangeHeader)
class ChangeHeaderAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'object_id', 'object_repr', 'change_type', 'username_snapshot', 'change_time']
    list_filter = ['change_type', 'content_type']
    search_fields = ['object_id', 'object_repr', 'username_snapshot']
    inlines = [ChangeItemInline]
