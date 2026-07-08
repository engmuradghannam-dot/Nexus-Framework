from apps.core.admin_site import admin_site
from .models import Project, Task, Milestone


@admin.register(Project, site=admin_site)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'status', 'priority', 'owner', 'progress',
                    'budget_utilization', 'start_date', 'end_date']
    list_filter = ['status', 'priority', 'branch']
    search_fields = ['name', 'code', 'description']
    date_hierarchy = 'start_date'


@admin.register(Task, site=admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'status', 'due_date', 'estimated_hours']
    list_filter = ['status']
    search_fields = ['title', 'description']


@admin.register(Milestone, site=admin_site)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'target_date', 'achieved_date']
    date_hierarchy = 'target_date'
