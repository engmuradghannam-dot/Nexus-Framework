from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Workflow(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class WorkflowStep(models.Model):
    ACTION_CHOICES = [
        ('approve', 'Approve/Reject'),
        ('review', 'Review'),
        ('notify', 'Notify'),
        ('condition', 'Condition'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='approve')
    approvers = models.ManyToManyField(User, blank=True, related_name='workflow_steps')
    approver_role = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    auto_approve_after = models.PositiveIntegerField(default=0, help_text="Hours to auto-approve")
    condition_field = models.CharField(max_length=255, blank=True)
    condition_value = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.workflow.name} - {self.name}"

class ApprovalRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
        ('cancelled', 'Cancelled'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='requests')
    current_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Generic relation to the object being approved
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

class ApprovalAction(models.Model):
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('commented', 'Commented'),
        ('delegated', 'Delegated'),
    ]

    request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='actions')
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='actions')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} {self.action} {self.request.title}"
