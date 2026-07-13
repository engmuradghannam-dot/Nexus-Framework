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
