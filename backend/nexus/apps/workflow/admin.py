from django.contrib import admin
from .models import Workflow, WorkflowStep, ApprovalRequest, ApprovalAction

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']

@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'name', 'order', 'action', 'is_required']
    list_filter = ['action', 'is_required']

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'workflow', 'requester', 'status', 'created_at']
    list_filter = ['status', 'workflow']

@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ['request', 'actor', 'action', 'created_at']
    list_filter = ['action']
