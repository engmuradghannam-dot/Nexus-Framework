"""Seed sample attendance + timesheets (idempotent)."""
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand

from apps.attendance.models import Attendance, Timesheet

EMPLOYEES = [
    ("E-3001", "محمد العتيبي"), ("E-3002", "نورة القحطاني"), ("E-3003", "راج كومار"),
]


class Command(BaseCommand):
    help = "Seed sample attendance & timesheets (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for d in range(5):  # last 5 days
            day = date.today() - timedelta(days=d)
            for i, (no, name) in enumerate(EMPLOYEES):
                if Attendance.objects.filter(employee_no=no, date=day).exists():
                    continue
                late = (d + i) % 4 == 0
                Attendance.objects.create(
                    employee_no=no, employee_name=name, date=day,
                    check_in=time(9, 15) if late else time(8, 0),
                    check_out=time(17, 0),
                    status="late" if late else "present",
                )
                n += 1
        if Timesheet.objects.count() == 0:
            for i, (no, name) in enumerate(EMPLOYEES):
                Timesheet.objects.create(
                    employee_name=name, date=date.today(),
                    project="نظام Nexus ERP", task="تطوير وحدة",
                    hours=[6, 7.5, 8][i], billable=True, description="عمل تطويري",
                )
                n += 1
        self.stdout.write(self.style.SUCCESS(f"Attendance/timesheets seeded: {n} new"))
