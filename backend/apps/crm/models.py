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
