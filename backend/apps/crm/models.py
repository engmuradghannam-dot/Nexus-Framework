from django.db import models

from apps.core.models import Company


class Lead(models.Model):
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Replied", "Replied"),
        ("Opportunity", "Opportunity"),
        ("Quotation", "Quotation"),
        ("Lost", "Lost"),
        ("Converted", "Converted"),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="leads")
    lead_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Open")
    source = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    score = models.PositiveSmallIntegerField(
        default=0, help_text="CRM-RULE-001: maintained by recalculate_score()."
    )

    def recalculate_score(self):
        """CRM-RULE-001: 0–100 from whatever rules Sales configured.

        With no rules configured the score stays 0 and no ranking is implied —
        an unscored lead is unscored, not a bad one.
        """
        rules = LeadScoringRule.objects.filter(company=self.company, is_active=True)
        total = sum((r.points for r in rules if r.matches(self)), 0)
        self.score = max(0, min(100, total))
        if self.pk:
            Lead.objects.filter(pk=self.pk).update(score=self.score)
        return self.score

    def score_breakdown(self):
        """Which rules fired, so a score can be explained rather than trusted."""
        rules = LeadScoringRule.objects.filter(company=self.company, is_active=True)
        return [
            {"rule": r.name, "points": r.points}
            for r in rules if r.matches(self)
        ]

    def __str__(self):
        return self.lead_name


# CRM-RULE-002: opportunities move forward through the funnel, never
# backwards. Lost is reachable from any open stage; Converted only from
# Quotation, because you can't win a deal you never quoted.
OPPORTUNITY_TRANSITIONS = {
    "Open": {"Quotation", "Lost"},
    "Quotation": {"Converted", "Lost"},
    "Converted": set(),
    "Lost": set(),
}
# Fields each stage requires before it can be entered.
OPPORTUNITY_STAGE_REQUIREMENTS = {
    "Quotation": ["expected_amount", "closing_date"],
    "Converted": ["customer_name", "expected_amount", "closing_date"],
}


class Opportunity(models.Model):
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Quotation", "Quotation"),
        ("Converted", "Converted"),
        ("Lost", "Lost"),
    ]
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="opportunities"
    )
    lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True)
    opportunity_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, blank=True)
    expected_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Open")
    closing_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.opportunity_name

    def check_stage_transition(self, new_status):
        """CRM-RULE-002: validate the sequence and the fields each stage needs.

        A pipeline that lets deals jump straight to Converted, or slide back to
        Open after being lost, reports numbers nobody can trust — which is what
        CRM-CTRL-003's pipeline audit is meant to rely on.
        """
        from django.core.exceptions import ValidationError

        if new_status == self.status:
            return
        allowed = OPPORTUNITY_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot move an opportunity from '{self.status}' to "
                f"'{new_status}'. Allowed: {', '.join(sorted(allowed)) or 'none'}."
            )
        missing = [
            f for f in OPPORTUNITY_STAGE_REQUIREMENTS.get(new_status, [])
            if not getattr(self, f, None)
        ]
        if missing:
            raise ValidationError(
                f"'{new_status}' requires {', '.join(missing)} to be set first."
            )


class LeadScoringRule(models.Model):
    """CRM-RULE-001: what makes a lead promising, as Sales decides.

    The spec says score 0–100 'based on engagement' and defines neither the
    signals nor their weights. Both are a sales judgement — what counts as
    engagement differs by what you sell — so Sales enters them here.

    Each rule tests one field on the Lead for a value and awards points. Scores
    are capped at 100, so weights can be tuned without anyone having to make
    them sum neatly.
    """

    MATCH_TYPES = [
        ("equals", "Equals"),
        ("not_empty", "Is filled in"),
        ("contains", "Contains"),
    ]
    company = models.ForeignKey(
        "core.CompanyProfile", on_delete=models.CASCADE, related_name="lead_scoring_rules"
    )
    name = models.CharField(max_length=100)
    field_name = models.CharField(
        max_length=50,
        help_text="Which Lead field this rule inspects, e.g. 'source', 'email'.",
    )
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES, default="not_empty")
    match_value = models.CharField(
        max_length=255, blank=True,
        help_text="The value to compare against. Unused for 'is filled in'.",
    )
    points = models.IntegerField(
        help_text="Points awarded when the rule matches. Negative is allowed."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-points", "name"]

    def __str__(self):
        return f"{self.name}: {self.points:+d} pts"

    def matches(self, lead):
        value = getattr(lead, self.field_name, None)
        if self.match_type == "not_empty":
            return bool(value)
        if value is None:
            return False
        if self.match_type == "equals":
            return str(value).strip().lower() == self.match_value.strip().lower()
        if self.match_type == "contains":
            return self.match_value.strip().lower() in str(value).lower()
        return False
