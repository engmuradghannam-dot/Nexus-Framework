"""Seed sample PMO data (portfolio, projects, tasks, milestones) — idempotent."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from apps.pmo.models import Milestone, Portfolio, Project, Task


class Command(BaseCommand):
    help = "Seed sample PMO data (idempotent)."

    def handle(self, *args, **options):
        if Project.objects.exists():
            self.stdout.write("PMO already has data — skipping.")
            return
        today = date.today()
        pf = Portfolio.objects.create(name="محفظة التحول الرقمي", status="active", budget=2000000)

        p1 = Project.objects.create(
            name="تطبيق ERP للعميل", code="PRJ-001", portfolio=pf, status="active",
            priority="high", start_date=today - timedelta(days=15), end_date=today + timedelta(days=45),
            budget=600000, spent=210000, progress=45,
            description="تنفيذ نظام ERP متكامل مع تدريب الفريق",
        )
        p2 = Project.objects.create(
            name="بوابة الموظفين الذاتية", code="PRJ-002", portfolio=pf, status="planning",
            priority="medium", start_date=today + timedelta(days=5), end_date=today + timedelta(days=70),
            budget=250000, spent=0, progress=5,
        )

        p1_tasks = [
            ("تحليل المتطلبات", "done", -12, 40, 42),
            ("تصميم قاعدة البيانات", "in_progress", 3, 32, 18),
            ("تطوير وحدة المحاسبة", "in_progress", 10, 60, 25),
            ("تطوير وحدة المخزون", "todo", 20, 50, 0),
            ("الاختبار وضمان الجودة", "todo", 35, 40, 0),
        ]
        for title, st, due_off, est, act in p1_tasks:
            Task.objects.create(project=p1, title=title, status=st,
                                due_date=today + timedelta(days=due_off),
                                estimated_hours=est, actual_hours=act)
        for title, st, due_off in [("جمع متطلبات الموظفين", "todo", 15), ("تصميم الواجهة", "todo", 30)]:
            Task.objects.create(project=p2, title=title, status=st, due_date=today + timedelta(days=due_off))

        Milestone.objects.create(project=p1, name="تسليم النسخة التجريبية", target_date=today + timedelta(days=20))
        Milestone.objects.create(project=p1, name="الإطلاق النهائي", target_date=today + timedelta(days=45))
        self.stdout.write(self.style.SUCCESS("PMO sample data seeded"))
