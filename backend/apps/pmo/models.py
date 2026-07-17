"""PMO Models - Project Management Office"""

from django.contrib.auth import get_user_model
from django.db import models

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
        related_name="managed_portfolios",
        verbose_name="Portfolio Manager",
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("active", "Active"),
            ("on_hold", "On Hold"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
        verbose_name="Status",
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    budget = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Budget"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Portfolio"
        verbose_name_plural = "Portfolios"

    def __str__(self):
        return self.name


class Project(models.Model):
    """Project model"""

    name = models.CharField(max_length=255, verbose_name="Project Name")
    code = models.CharField(max_length=50, blank=True, verbose_name="Project Code")
    description = models.TextField(blank=True, verbose_name="Description")
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="projects",
        null=True,
        blank=True,
        verbose_name="Portfolio",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_projects",
        verbose_name="Project Owner",
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
        verbose_name="Project Manager",
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("planning", "Planning"),
            ("active", "Active"),
            ("on_hold", "On Hold"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        default="planning",
        verbose_name="Status",
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        default="medium",
        verbose_name="Priority",
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    actual_start_date = models.DateField(
        null=True, blank=True, verbose_name="Actual Start Date"
    )
    actual_end_date = models.DateField(
        null=True, blank=True, verbose_name="Actual End Date"
    )
    budget = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Budget"
    )
    spent = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name="Spent"
    )
    progress = models.PositiveIntegerField(
        default=0,
        verbose_name="Progress %",
        help_text="Auto-computed from task completion ratio once the project has "
        "tasks (see recalculate_progress); stays manually editable for projects "
        "with no tasks yet.",
    )
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="Branch",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name

    @property
    def budget_utilization(self):
        if self.budget and self.budget > 0:
            return round((self.spent / self.budget) * 100, 2)
        return 0

    @property
    def is_overdue(self):
        from datetime import date

        if self.end_date and self.status not in ["completed", "cancelled"]:
            return date.today() > self.end_date
        return False

    def recalculate_progress(self):
        """Recompute progress % from task completion (done / non-cancelled tasks).

        Called via the Task post_save/post_delete signal. A no-op when the
        project has no tasks yet, so the manually-entered progress value
        keeps working until tasks exist to derive it from.
        """
        tasks = list(self.tasks.exclude(status="cancelled"))
        if not tasks:
            return
        done = sum(1 for t in tasks if t.status == "done")
        progress = round((done / len(tasks)) * 100)
        Project.objects.filter(pk=self.pk).update(progress=progress)
        self.progress = progress


class Task(models.Model):
    """Task model for projects"""

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("review", "Review"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="tasks", verbose_name="Project"
    )
    title = models.CharField(max_length=255, verbose_name="Title")
    description = models.TextField(blank=True, verbose_name="Description")
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Assignee",
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="todo", verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium", verbose_name="Priority"
    )
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
        verbose_name="Parent Task",
    )
    milestone = models.ForeignKey(
        "Milestone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Milestone",
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")
    estimated_hours = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, verbose_name="Estimated Hours"
    )
    actual_hours = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, verbose_name="Actual Hours"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title


class Milestone(models.Model):
    """Milestone model for projects"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
        verbose_name="Project",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")
    target_date = models.DateField(null=True, blank=True, verbose_name="Target Date")
    achieved_date = models.DateField(
        null=True, blank=True, verbose_name="Achieved Date"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        ordering = ["target_date"]
        verbose_name = "Milestone"
        verbose_name_plural = "Milestones"

    def __str__(self):
        return self.name

    @property
    def is_achieved(self):
        return self.achieved_date is not None

    @property
    def is_overdue(self):
        from datetime import date

        if self.target_date and not self.is_achieved:
            return date.today() > self.target_date
        return False
