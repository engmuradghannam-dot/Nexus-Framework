"""Attendance (check-in/out) and timesheets (hours logged)."""
from datetime import datetime

from django.db import models


class Attendance(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    STATUS = [("present", "Present"), ("late", "Late"), ("absent", "Absent"), ("leave", "On Leave")]

    employee_no = models.CharField(max_length=50, blank=True)
    employee_name = models.CharField(max_length=200)
    date = models.DateField(db_index=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="present")
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "attendance"
        ordering = ["-date", "employee_name"]
        unique_together = ["employee_no", "date"]

    def recompute(self):
        if self.check_in and self.check_out:
            t0 = datetime.combine(self.date, self.check_in)
            t1 = datetime.combine(self.date, self.check_out)
            self.hours = round(max((t1 - t0).total_seconds() / 3600, 0), 2)

    def save(self, *args, **kwargs):
        self.recompute()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_name} {self.date}"


class Timesheet(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    employee_name = models.CharField(max_length=200)
    date = models.DateField(db_index=True)
    project = models.CharField(max_length=200, blank=True)
    task = models.CharField(max_length=200, blank=True)
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    billable = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "timesheets"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee_name} {self.date} ({self.hours}h)"
