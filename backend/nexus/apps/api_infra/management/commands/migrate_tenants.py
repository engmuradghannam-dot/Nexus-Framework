from django.core.management.base import BaseCommand

from nexus.apps.api_infra.tenancy import Tenant


class Command(BaseCommand):
    help = "Provision (if needed) and run migrations against every active tenant's database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema', dest='schema', default=None,
            help='Only migrate the tenant with this schema_name.',
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.filter(is_active=True)
        if options['schema']:
            tenants = tenants.filter(schema_name=options['schema'])

        if not tenants.exists():
            self.stdout.write('No active tenants to migrate.')
            return

        for tenant in tenants:
            self.stdout.write(f"Provisioning/migrating tenant '{tenant.schema_name}'...")
            try:
                alias = tenant.provision_database()
            except Exception as exc:
                self.stderr.write(self.style.ERROR(
                    f"  failed to provision database for '{tenant.schema_name}': {exc}"))
                continue
            self.stdout.write(self.style.SUCCESS(f"  {tenant.schema_name} -> {alias} OK"))
