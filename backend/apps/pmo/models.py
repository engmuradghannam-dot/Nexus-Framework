from django.db import models
from django.conf import settings
import uuid


class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=2)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    progress = models.PositiveSmallIntegerField(default=0, help_text='0-100%')
    branch = models.ForeignKey(
        'core.Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pmo_projects'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def budget_utilization(self):
        if self.budget == 0:
            return 0
        return round((self.spent / self.budget) * 100, 2)

    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.end_date < timezone.now().date() and self.status not in ['completed', 'cancelled']


class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('done', 'Done'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(default=0)
    actual_hours = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pmo_tasks'
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title


class Milestone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    target_date = models.DateField()
    achieved_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'pmo_milestones'
        ordering = ['target_date']

    def __str__(self):
        return self.name

    @property
    def is_achieved(self):
        return self.achieved_date is not None

    @property
    def is_overdue(self):
        from django.utils import timezone
        return not self.is_achieved and self.target_date < timezone.now().date()
