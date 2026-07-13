"""HR extras: expense claims, loans, recruitment, appraisals + EOS gratuity calc."""
from decimal import Decimal

from django.db import models


class TenantBase(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")

    class Meta:
        abstract = True


class ExpenseClaim(TenantBase):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("paid", "Paid")]
    employee_name = models.CharField(max_length=150)
    date = models.DateField()
    category = models.CharField(max_length=80, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")

    class Meta:
        db_table = "hr_expense_claims"
        ordering = ["-date", "-id"]


class EmployeeLoan(TenantBase):
    STATUS = [("active", "Active"), ("settled", "Settled")]
    employee_name = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    installments = models.PositiveSmallIntegerField(default=1)
    paid_installments = models.PositiveSmallIntegerField(default=0)
    start_date = models.DateField()
    status = models.CharField(max_length=8, choices=STATUS, default="active")

    class Meta:
        db_table = "hr_employee_loans"
        ordering = ["-start_date"]

    @property
    def monthly(self):
        return (Decimal(self.amount or 0) / max(self.installments, 1)).quantize(Decimal("0.01"))

    @property
    def remaining(self):
        return (Decimal(self.amount or 0) - self.monthly * self.paid_installments).quantize(Decimal("0.01"))


class JobOpening(TenantBase):
    STATUS = [("open", "Open"), ("closed", "Closed")]
    title = models.CharField(max_length=150)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    openings = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=8, choices=STATUS, default="open")

    class Meta:
        db_table = "hr_job_openings"
        ordering = ["-id"]


class JobApplicant(TenantBase):
    STAGES = [("applied", "Applied"), ("screening", "Screening"), ("interview", "Interview"), ("offer", "Offer"), ("hired", "Hired"), ("rejected", "Rejected")]
    opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name="applicants")
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    stage = models.CharField(max_length=10, choices=STAGES, default="applied")
    rating = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "hr_job_applicants"
        ordering = ["-id"]


class Appraisal(TenantBase):
    employee_name = models.CharField(max_length=150)
    period = models.CharField(max_length=40)
    score = models.DecimalField(max_digits=4, decimal_places=1, default=0)  # 0..5
    goals = models.CharField(max_length=255, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        db_table = "hr_appraisals"
        ordering = ["-id"]


def end_of_service(last_wage, years, reason="termination"):
    """Saudi Labor Law gratuity: first 5 years -> half-month/yr, beyond -> full
    month/yr. Resignation scales the benefit by service length."""
    w = Decimal(str(last_wage or 0))
    y = Decimal(str(years or 0))
    first = min(y, Decimal(5)) * (w / 2)
    beyond = max(y - Decimal(5), Decimal(0)) * w
    gratuity = first + beyond
    if reason == "resignation":
        if y < 2:
            factor = Decimal(0)
        elif y < 5:
            factor = Decimal(1) / Decimal(3)
        elif y < 10:
            factor = Decimal(2) / Decimal(3)
        else:
            factor = Decimal(1)
        gratuity = gratuity * factor
    return gratuity.quantize(Decimal("0.01"))
