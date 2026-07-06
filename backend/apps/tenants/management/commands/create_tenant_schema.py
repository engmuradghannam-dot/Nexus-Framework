"""
Management command to create and migrate tenant schemas.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = 'Create PostgreSQL schema and run migrations for a tenant'

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str, nargs='?', help='Tenant schema name (optional, migrates all if omitted)')
        parser.add_argument('--all', action='store_true', help='Migrate all tenant schemas')
        parser.add_argument('--create-only', action='store_true', help='Only create schema, do not migrate')

    def handle(self, *args, **options):
        if options['all']:
            self._migrate_all()
        elif options['schema_name']:
            self._migrate_single(options['schema_name'], not options['create_only'])
        else:
            self.stdout.write(self.style.ERROR('Provide schema_name or use --all'))

    def _migrate_single(self, schema_name, run_migrations=True):
        self.stdout.write(f"Processing schema: {schema_name}")

        # Create schema
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        self.stdout.write(self.style.SUCCESS(f'  Created schema: {schema_name}'))

        if not run_migrations:
            return

        # Set search path
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema_name}", public')

        # Run migrations for tenant apps
        tenant_apps = [
            'apps.core', 'apps.accounts', 'apps.inventory',
            'apps.buying', 'apps.selling', 'apps.manufacturing',
            'apps.hr', 'apps.crm', 'apps.projects', 'apps.assets',
            'apps.workflow',
        ]

        for app in tenant_apps:
            try:
                call_command('migrate', app, '--run-syncdb', verbosity=0)
                self.stdout.write(f'  Migrated: {app}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Skip {app}: {e}'))

        self.stdout.write(self.style.SUCCESS('Done!'))

    def _migrate_all(self):
        tenants = Tenant.objects.all()
        for tenant in tenants:
            self._migrate_single(tenant.schema_name)
