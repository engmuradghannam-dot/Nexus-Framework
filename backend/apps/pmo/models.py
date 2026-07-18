"""PMO Models - Project Management Office"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
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

    def calculate_critical_path(self):
        """PRJ-RULE-003: forward/backward pass over the task network (CPM).

        Day numbers are relative to project start (day 0), so the result stays
        valid regardless of calendar dates — which are frequently missing on
        these tasks. Cancelled tasks are excluded: they can't hold up anything.

        Returns the list of critical tasks (slack == 0). Writes early/late
        start/finish, slack and is_critical to every task in the network.
        """
        tasks = list(
            self.tasks.exclude(status="Cancelled").prefetch_related("predecessors")
        )
        if not tasks:
            return []
        by_id = {t.pk: t for t in tasks}
        preds = {
            t.pk: [p.pk for p in t.predecessors.all() if p.pk in by_id] for t in tasks
        }

        # Topological order. A cycle would loop forever, so detect it instead.
        order, visiting, done = [], set(), set()

        def visit(pk):
            if pk in done:
                return
            if pk in visiting:
                raise DjangoValidationError(
                    f"Task dependencies contain a cycle involving "
                    f"'{by_id[pk].title}'; the critical path is undefined."
                )
            visiting.add(pk)
            for dep in preds[pk]:
                visit(dep)
            visiting.discard(pk)
            done.add(pk)
            order.append(pk)

        for pk in by_id:
            visit(pk)

        # Forward pass
        es, ef = {}, {}
        for pk in order:
            t = by_id[pk]
            es[pk] = max((ef[d] for d in preds[pk]), default=0)
            ef[pk] = es[pk] + max(int(t.duration_days or 0), 0)

        project_finish = max(ef.values())

        # Backward pass
        succs = {pk: [] for pk in by_id}
        for pk, deps in preds.items():
            for d in deps:
                succs[d].append(pk)
        lf, ls = {}, {}
        for pk in reversed(order):
            t = by_id[pk]
            lf[pk] = min((ls[s_] for s_ in succs[pk]), default=project_finish)
            ls[pk] = lf[pk] - max(int(t.duration_days or 0), 0)

        critical = []
        for pk, t in by_id.items():
            t.early_start, t.early_finish = es[pk], ef[pk]
            t.late_start, t.late_finish = ls[pk], lf[pk]
            t.slack = ls[pk] - es[pk]
            t.is_critical = t.slack == 0
            if t.is_critical:
                critical.append(t)
        Task.objects.bulk_update(
            tasks,
            ["early_start", "early_finish", "late_start", "late_finish",
             "slack", "is_critical"],
        )
        return sorted(critical, key=lambda t: (t.early_start, t.pk))

    @property
    def critical_path_length(self):
        """Project duration in days along the longest dependent chain."""
        from django.db.models import Max

        return self.tasks.exclude(status="Cancelled").aggregate(
            m=Max("early_finish")
        )["m"]

    @property
    def burn_rate(self):
        """PRJ-RULE-002: budget consumed per elapsed day.

        Returns None before the project starts or if it has no start date —
        dividing by zero elapsed days would report an infinite burn on day one.
        """
        from datetime import date

        start = self.actual_start_date or self.start_date
        if not start:
            return None
        elapsed = (date.today() - start).days
        if elapsed <= 0:
            return None
        return (Decimal(self.spent or 0) / Decimal(elapsed)).quantize(Decimal("0.01"))

    def check_milestone_gate(self, task):
        """PRJ-CTRL-002: a task can't start while the milestone gating it is
        still open.

        Milestone acts as the phase gate: work assigned to a later milestone
        must wait for the earlier ones to be signed off. Tasks with no milestone
        are ungated.
        """
        if task.milestone_id is None:
            return
        gate = task.milestone
        if gate.target_date is None:
            return
        earlier_open = self.milestones.filter(
            target_date__lt=gate.target_date, achieved_date__isnull=True
        ).exclude(pk=gate.pk)
        if earlier_open.exists():
            names = ", ".join(m.name for m in earlier_open)
            raise DjangoValidationError(
                f"Cannot start '{task.title}': earlier milestone(s) not yet "
                f"approved — {names}."
            )

    def closure_blockers(self):
        """PRJ-RULE-005: what still stands between this project and Completed."""
        blockers = []
        open_tasks = self.tasks.exclude(status__in=["Done", "Cancelled"]).count()
        if open_tasks:
            blockers.append(f"{open_tasks} task(s) still open")
        unmet = self.milestones.filter(achieved_date__isnull=True).count()
        if unmet:
            blockers.append(f"{unmet} milestone(s) not achieved")
        if self.budget and Decimal(self.spent or 0) > Decimal(self.budget):
            blockers.append(
                f"budget overrun: spent {self.spent} against budget {self.budget}"
            )
        return blockers

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
    duration_days = models.PositiveIntegerField(
        default=1,
        help_text="PRJ-RULE-003: working span used by the critical path calculation.",
    )
    predecessors = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="successors",
        help_text="Tasks that must finish before this one starts (finish-to-start).",
    )
    early_start = models.PositiveIntegerField(null=True, blank=True, editable=False)
    early_finish = models.PositiveIntegerField(null=True, blank=True, editable=False)
    late_start = models.PositiveIntegerField(null=True, blank=True, editable=False)
    late_finish = models.PositiveIntegerField(null=True, blank=True, editable=False)
    slack = models.IntegerField(null=True, blank=True, editable=False)
    is_critical = models.BooleanField(default=False, editable=False)
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


def check_resource_allocation(assignee, task, capacity_hours_per_day=8):
    """PRJ-CTRL-003: nobody is allocated beyond 100% of their capacity.

    Compares the assignee's committed hours per day across every overlapping,
    non-finished task against a working-day capacity. Tasks without both dates
    or without estimated hours can't be scheduled against capacity, so they are
    skipped rather than guessed at.
    """
    from decimal import Decimal

    if assignee is None or not task.start_date or not task.due_date:
        return
    if not task.estimated_hours:
        return

    def load(t):
        span = max((t.due_date - t.start_date).days + 1, 1)
        return Decimal(t.estimated_hours) / Decimal(span)

    overlapping = Task.objects.filter(
        assignee=assignee,
        start_date__lte=task.due_date,
        due_date__gte=task.start_date,
    ).exclude(status__in=["Done", "Cancelled"]).exclude(pk=task.pk)
    committed = sum(
        (load(t) for t in overlapping if t.start_date and t.due_date and t.estimated_hours),
        Decimal(0),
    )
    total = committed + load(task)
    if total > Decimal(capacity_hours_per_day):
        raise DjangoValidationError(
            f"Resource over-allocated: {assignee} would be committed to "
            f"{total.quantize(Decimal('0.01'))}h/day against a capacity of "
            f"{capacity_hours_per_day}h."
        )


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


class ChangeRequest(models.Model):
    """PRJ-CTRL-005: a formal record for any change to a project's scope,
    budget or dates.

    Project.budget and end_date could be edited freely by anyone, so scope creep
    left no trace: the plan simply became whatever it had most recently been
    changed to, and nobody could tell what had been agreed originally.
    """

    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="change_requests"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    justification = models.TextField(
        blank=True, help_text="Why the change is needed. Required to submit."
    )
    budget_delta = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Change to the project budget. Negative reduces it.",
    )
    end_date_delta_days = models.IntegerField(
        default=0, help_text="Change to the project end date, in days."
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="change_requests_raised",
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="change_requests_approved",
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Draft")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.project.code}: {self.title}"

    def submit(self):
        if self.status != "Draft":
            raise DjangoValidationError(
                f"Only a draft change request can be submitted (this one is "
                f"'{self.status}')."
            )
        if not self.justification.strip():
            raise DjangoValidationError(
                "A change request needs a justification before it can be submitted."
            )
        if self.budget_delta == 0 and self.end_date_delta_days == 0:
            raise DjangoValidationError(
                "A change request must actually change something."
            )
        self.status = "Submitted"
        self.save(update_fields=["status"])
        return True, "تم إرسال طلب التغيير / Change request submitted"

    def approve(self, approver):
        """Apply the change to the project — the only sanctioned path.

        The requester cannot approve their own change: a change control where
        the person asking is the person agreeing controls nothing.
        """
        from datetime import timedelta

        from django.db import transaction as db_transaction
        from django.utils import timezone

        if self.status != "Submitted":
            raise DjangoValidationError(
                f"Only a submitted change request can be approved (this one is "
                f"'{self.status}')."
            )
        if approver is None:
            raise DjangoValidationError("An approver is required.")
        if self.requested_by_id and approver.pk == self.requested_by_id:
            raise DjangoValidationError(
                "The requester cannot approve their own change request."
            )
        with db_transaction.atomic():
            project = self.project
            if self.budget_delta:
                project.budget = Decimal(project.budget or 0) + Decimal(self.budget_delta)
            if self.end_date_delta_days and project.end_date:
                project.end_date = project.end_date + timedelta(days=self.end_date_delta_days)
            project.save(update_fields=["budget", "end_date"])
            self.status = "Approved"
            self.approved_by = approver
            self.decided_at = timezone.now()
            self.save(update_fields=["status", "approved_by", "decided_at"])
        return True, "تم اعتماد طلب التغيير / Change request approved"

    def reject(self, approver):
        from django.utils import timezone

        if self.status != "Submitted":
            raise DjangoValidationError("Only a submitted change request can be rejected.")
        self.status = "Rejected"
        self.approved_by = approver
        self.decided_at = timezone.now()
        self.save(update_fields=["status", "approved_by", "decided_at"])
        return True, "تم رفض طلب التغيير / Change request rejected"
