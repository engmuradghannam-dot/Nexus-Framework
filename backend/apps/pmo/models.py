"""PMO Models - Project Management Office"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Portfolio(models.Model):
    """Portfolio of projects"""
    name = models.CharField(max_length=255, verbose_name="Portfolio Name")
    description = models.TextField(blank=True, verbose_name="Description")
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_portfolios',
        verbose_name="Portfolio Manager"
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='active',
        verbose_name="Status"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Budget"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Portfolio"
        verbose_name_plural = "Portfolios"

    def __str__(self):
        return self.name


class Project(models.Model):
    """Project model"""
    name = models.CharField(max_length=255, verbose_name="Project Name")
    description = models.TextField(blank=True, verbose_name="Description")
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='projects',
        null=True,
        blank=True,
        verbose_name="Portfolio"
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
        verbose_name="Project Manager"
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('planning', 'Planning'),
            ('active', 'Active'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='planning',
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        default='medium',
        verbose_name="Priority"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Budget"
    )
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name="Progress %"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name
