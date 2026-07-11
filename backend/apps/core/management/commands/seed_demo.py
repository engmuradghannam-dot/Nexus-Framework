"""Seed the database with realistic demo data for a live demonstration.

Idempotent: uses get_or_create on natural keys, safe to run every deploy.
Populates the modules whose pages read from the backend (Industry, PMO) plus
a few Regulatory / AI records for their dashboards.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed realistic demo data (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        actor = (
            User.objects.filter(is_superuser=True).order_by("date_joined").first()
            or User.objects.order_by("date_joined").first()
        )

        counts = {}
        counts.update(self._seed_industry(actor))
        counts.update(self._seed_pmo(actor))
        counts.update(self._seed_regulatory(actor))
        counts.update(self._seed_ai(actor))

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded: "
                + ", ".join(f"{k}={v}" for k, v in counts.items() if v)
            )
        )

    # ── Industry ────────────────────────────────────────────
    def _seed_industry(self, actor):
        from apps.industry.models import Company, IndustryVertical, Sector

        vertical, _ = IndustryVertical.objects.get_or_create(
            code="TECH",
            defaults={
                "name": "Technology",
                "description": "Technology and software companies",
                "created_by": actor,
            },
        )
        sectors = {}
        for name, code in [("Software", "SW"), ("Fintech", "FIN"), ("Hardware", "HW")]:
            s, _ = Sector.objects.get_or_create(
                code=code,
                industry_vertical=vertical,
                defaults={"name": name},
            )
            sectors[code] = s

        demo_companies = [
            ("Aramco Digital", "ARD", "FIN", "Riyadh", 120_000_000, 900_000_000),
            ("STC Solutions", "STCS", "SW", "Riyadh", 80_000_000, 400_000_000),
            ("Jahez Tech", "JHZ", "SW", "Jeddah", 25_000_000, 150_000_000),
            ("Nexus Systems", "NXS", "HW", "Dammam", 15_000_000, 60_000_000),
            ("Tamara Fintech", "TMR", "FIN", "Riyadh", 40_000_000, 220_000_000),
            ("Mrsool Cloud", "MRS", "SW", "Riyadh", 18_000_000, 90_000_000),
        ]
        n = 0
        for name, ticker, sec, hq, revenue, mcap in demo_companies:
            _, created = Company.objects.get_or_create(
                ticker=ticker,
                defaults={
                    "name": name,
                    "industry_vertical": vertical,
                    "sector": sectors.get(sec),
                    "headquarters": hq,
                    "revenue": Decimal(revenue),
                    "market_cap": Decimal(mcap),
                    "currency": "SAR",
                },
            )
            n += 1 if created else 0
        return {"industries": IndustryVertical.objects.count(), "companies": n}

    # ── PMO ─────────────────────────────────────────────────
    def _seed_pmo(self, actor):
        from apps.pmo.models import Milestone, Portfolio, Project, Task

        portfolio, _ = Portfolio.objects.get_or_create(
            name="Digital Transformation",
            defaults={
                "description": "Enterprise digital transformation programme",
                "manager": actor,
                "status": "active",
                "start_date": date.today() - timedelta(days=90),
                "end_date": date.today() + timedelta(days=275),
                "budget": Decimal("5000000"),
            },
        )

        demo_projects = [
            ("ERP Rollout", "PRJ-001", "active", "high", 45, 5_000_000, 2_250_000),
            ("E-commerce Platform", "PRJ-002", "planning", "medium", 10, 1_800_000, 180_000),
            ("Mobile App Revamp", "PRJ-003", "active", "high", 70, 900_000, 630_000),
            ("Data Warehouse", "PRJ-004", "on_hold", "low", 25, 1_200_000, 300_000),
        ]
        projects = []
        for name, code, status, priority, progress, budget, spent in demo_projects:
            p, _ = Project.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "portfolio": portfolio,
                    "owner": actor,
                    "manager": actor,
                    "status": status,
                    "priority": priority,
                    "progress": progress,
                    "start_date": date.today() - timedelta(days=60),
                    "end_date": date.today() + timedelta(days=120),
                    "budget": Decimal(budget),
                    "spent": Decimal(spent),
                },
            )
            projects.append(p)

        tasks = [
            ("Requirements gathering", "done"),
            ("System design", "in_progress"),
            ("Development", "todo"),
            ("UAT & rollout", "todo"),
        ]
        nt = 0
        for p in projects:
            for i, (title, status) in enumerate(tasks):
                _, created = Task.objects.get_or_create(
                    project=p,
                    title=title,
                    defaults={
                        "assignee": actor,
                        "status": status,
                        "due_date": date.today() + timedelta(days=20 * (i + 1)),
                        "estimated_hours": Decimal("40"),
                    },
                )
                nt += 1 if created else 0
            Milestone.objects.get_or_create(
                project=p,
                name="Go-Live",
                defaults={"target_date": date.today() + timedelta(days=120)},
            )
        return {
            "portfolios": Portfolio.objects.count(),
            "projects": len(projects),
            "tasks": nt,
        }

    # ── Regulatory ──────────────────────────────────────────
    def _seed_regulatory(self, actor):
        try:
            from apps.regulatory.models import Regulation
        except Exception:
            return {}
        demo = [
            ("ZATCA E-Invoicing", "ZATCA-01", "SA", "high"),
            ("GOSI Compliance", "GOSI-01", "SA", "medium"),
            ("PDPL Data Privacy", "PDPL-01", "SA", "high"),
            ("Nitaqat Saudization", "NIT-01", "SA", "medium"),
        ]
        n = 0
        for title, code, juris, severity in demo:
            try:
                _, created = Regulation.objects.get_or_create(
                    code=code,
                    defaults={
                        "title": title,
                        "jurisdiction": juris,
                        "severity": severity,
                        "effective_date": date(2024, 1, 1),
                        "description": f"{title} regulatory requirement.",
                        "created_by": actor,
                    },
                )
                n += 1 if created else 0
            except Exception:
                pass
        return {"regulations": n}

    # ── AI ──────────────────────────────────────────────────
    def _seed_ai(self, actor):
        try:
            from apps.ai_module.models import AIModel
        except Exception:
            return {}
        model_type = AIModel._meta.get_field("model_type").choices[0][0]
        demo = [
            ("Demand Forecaster", "1.2.0", 0.92),
            ("Churn Predictor", "1.0.0", 0.88),
            ("Anomaly Detector", "2.1.0", 0.95),
        ]
        n = 0
        for name, version, acc in demo:
            try:
                _, created = AIModel.objects.get_or_create(
                    name=name,
                    version=version,
                    defaults={
                        "model_type": model_type,
                        "owner": actor,
                        "accuracy": acc,
                    },
                )
                n += 1 if created else 0
            except Exception:
                pass
        return {"ai_models": n}
