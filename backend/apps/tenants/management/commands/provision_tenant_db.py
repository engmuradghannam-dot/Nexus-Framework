"""Provision a tenant's own database: register it and run migrations into it.

Usage: manage.py provision_tenant_db <tenant_id>

The tenant must already have database_url set. This registers the connection and
runs migrate against that alias, so the tenant's dedicated database gets the full
schema (minus the shared apps, which the router keeps in default).
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Tenant
from apps.tenants.routing import register_tenant_db


class Command(BaseCommand):
    help = "Register and migrate a tenant's dedicated database."

    def add_arguments(self, parser):
        parser.add_argument("tenant_id", type=int)

    def handle(self, *args, **options):
        try:
            tenant = Tenant.objects.get(pk=options["tenant_id"])
        except Tenant.DoesNotExist:
            raise CommandError("No such tenant.")
        if not tenant.database_url:
            raise CommandError(
                f"Tenant '{tenant.name}' has no database_url — it uses the shared "
                f"default database and needs no provisioning."
            )
        alias = register_tenant_db(tenant)
        self.stdout.write(f"Registered '{alias}'. Migrating…")
        call_command("migrate", database=alias, verbosity=1)
        self.stdout.write(self.style.SUCCESS(
            f"Tenant '{tenant.name}' database ready ({alias})."
        ))
