from django.contrib import admin
from .models import Workflow, WorkflowState, WorkflowTransition

admin.site.register(Workflow)
admin.site.register(WorkflowState)
admin.site.register(WorkflowTransition)
