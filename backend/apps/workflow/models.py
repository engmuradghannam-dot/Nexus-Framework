from django.db import models
from django.contrib.contenttypes.models import ContentType

class Workflow(models.Model):
    name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WorkflowState(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='states')
    state_name = models.CharField(max_length=100)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    def __str__(self):
        return self.state_name

class WorkflowTransition(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='transitions')
    from_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='transitions_from')
    to_state = models.ForeignKey(WorkflowState, on_delete=models.CASCADE, related_name='transitions_to')
    action = models.CharField(max_length=100)
    allowed_roles = models.CharField(max_length=255, blank=True)
