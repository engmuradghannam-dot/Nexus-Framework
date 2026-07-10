import uuid

from django.conf import settings
from django.db import models


class Regulation(models.Model):
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("under_review", "Under Review"),
        ("superseded", "Superseded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    code = models.CharField(max_length=50, unique=True)
    jurisdiction = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    effective_date = models.DateField()
    review_date = models.DateField(null=True, blank=True)
    description = models.TextField()
    document_url = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_regulations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regulatory_regulations"
        ordering = ["-effective_date"]

    def __str__(self):
        return f"{self.code} - {self.title}"

    @property
    def days_until_review(self):
        from django.utils import timezone

        if not self.review_date:
            return None
        delta = self.review_date - timezone.now().date()
        return delta.days

    @property
    def is_overdue(self):
        from django.utils import timezone

        return self.review_date and self.review_date < timezone.now().date()


class ComplianceCheck(models.Model):
    RESULT_CHOICES = [
        ("pass", "Pass"),
        ("fail", "Fail"),
        ("partial", "Partial"),
        ("pending", "Pending"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    regulation = models.ForeignKey(
        Regulation, on_delete=models.CASCADE, related_name="compliance_checks"
    )
    branch = models.ForeignKey(
        "core.Branch", on_delete=models.CASCADE, related_name="compliance_checks"
    )
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="pending")
    score = models.PositiveSmallIntegerField(default=0, help_text="0-100")
    findings = models.TextField(blank=True)
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audited_checks",
    )
    checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regulatory_compliance_checks"
        ordering = ["-checked_at"]
        unique_together = ["regulation", "branch"]

    def __str__(self):
        return f"{self.regulation.code} @ {self.branch.name}"


class Risk(models.Model):
    LIKELIHOOD_CHOICES = [
        (1, "Rare"),
        (2, "Unlikely"),
        (3, "Possible"),
        (4, "Likely"),
        (5, "Almost Certain"),
    ]
    IMPACT_CHOICES = [
        (1, "Negligible"),
        (2, "Minor"),
        (3, "Moderate"),
        (4, "Major"),
        (5, "Catastrophic"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("mitigated", "Mitigated"),
        ("accepted", "Accepted"),
        ("closed", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    likelihood = models.PositiveSmallIntegerField(choices=LIKELIHOOD_CHOICES)
    impact = models.PositiveSmallIntegerField(choices=IMPACT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    mitigation_plan = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_risks"
    )
    related_regulation = models.ForeignKey(
        Regulation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "regulatory_risks"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    @property
    def risk_level(self):
        score = self.risk_score
        if score <= 4:
            return "Low"
        elif score <= 9:
            return "Medium"
        elif score <= 14:
            return "High"
        return "Critical"
