from django.core.validators import MinLengthValidator
from django.db import models
from nexus.apps.core.models import Company, Branch
from nexus.apps.core.validators import alphanumeric_validator

class Regulation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('expired', 'Expired'),
    ]

    title = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=100, unique=True, validators=[alphanumeric_validator])
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='regulations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.effective_date and self.expiry_date and self.expiry_date < self.effective_date:
            raise ValidationError('Expiry date must be on or after the effective date')

class ComplianceCheck(models.Model):
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('pending', 'Pending'),
    ]

    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='checks')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='compliance_checks')
    checked_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, db_constraint=False)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.regulation.title} - {self.branch.name}"
