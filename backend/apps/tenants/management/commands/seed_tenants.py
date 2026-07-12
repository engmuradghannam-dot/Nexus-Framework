"""Seed a default tenant (idempotent)."""
from django.core.management.base import BaseCommand

from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Seed default tenants (idempotent)."

    def handle(self, *args, **options):
        data = [
            ("Nexus Demo", "nexus-demo", "demo", "enterprise"),
            ("شركة الأفق", "al-ufuq", "ufuq", "pro"),
        ]
        for name, slug, sub, plan in data:
            Tenant.objects.get_or_create(
                slug=slug, defaults={"name": name, "subdomain": sub, "plan": plan})
        self.stdout.write(self.style.SUCCESS(f"Tenants ensured: {Tenant.objects.count()}"))
