from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models

from nexus.apps.core.models import Company, Branch

class Project(models.Model):
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date must be on or after the start date')

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, db_constraint=False)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    @property
    def name(self):
        # Back-compat alias: some read-only views (Gantt/timeline) expect .name
        return self.title

    @property
    def end_date(self):
        # Back-compat alias: some read-only views (Gantt/timeline) expect .end_date
        return self.due_date

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValidationError('Due date must be on or after the start date')

class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True)
    target_date = models.DateField()
    achieved = models.BooleanField(default=False)
    achieved_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"
