from django.contrib import admin
from .models import Project, Task, Milestone


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'priority', 'owner', 'progress',
                    'budget_utilization', 'is_overdue', 'start_date', 'end_date']
    list_filter = ['status', 'priority', 'branch']
    search_fields = ['name', 'code', 'description']
    date_hierarchy = 'start_date'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'status', 'due_date', 'estimated_hours']
    list_filter = ['status']
    search_fields = ['title', 'description']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'target_date', 'achieved_date', 'is_overdue']
    list_filter = ['is_overdue']
    date_hierarchy = 'target_date'
