from django.contrib import admin
from .models import Project, Task, Milestone

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'company']
    search_fields = ['name']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'priority', 'completed', 'due_date']
    list_filter = ['priority', 'completed']
    search_fields = ['title']

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'target_date', 'achieved']
    list_filter = ['achieved']
