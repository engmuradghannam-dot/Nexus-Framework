from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.hr_extras.models import (Appraisal, EmployeeLoan, ExpenseClaim,
                                   JobApplicant, JobOpening)


class Command(BaseCommand):
    help = "Seed sample HR extras data (idempotent)."

    def handle(self, *args, **options):
        if not ExpenseClaim.objects.exists():
            ExpenseClaim.objects.create(employee_name="أحمد العتيبي", date=date.today(), category="سفر", amount=1200, description="رحلة عمل جدة")
            ExpenseClaim.objects.create(employee_name="سارة القحطاني", date=date.today() - timedelta(days=3), category="ضيافة", amount=450, status="approved")
        if not EmployeeLoan.objects.exists():
            EmployeeLoan.objects.create(employee_name="أحمد العتيبي", amount=12000, installments=12, paid_installments=3, start_date=date.today() - timedelta(days=90))
        if not JobOpening.objects.exists():
            jo = JobOpening.objects.create(title="محاسب أول", department="المالية", location="الرياض", openings=2)
            JobApplicant.objects.create(opening=jo, name="خالد الشمري", email="k@example.com", stage="interview", rating=4)
            JobApplicant.objects.create(opening=jo, name="نورة الحربي", email="n@example.com", stage="screening", rating=3)
        if not Appraisal.objects.exists():
            Appraisal.objects.create(employee_name="سارة القحطاني", period="2025-H2", score=4.5, goals="تطوير التقارير المالية")
        self.stdout.write(self.style.SUCCESS("HR extras seeded"))
