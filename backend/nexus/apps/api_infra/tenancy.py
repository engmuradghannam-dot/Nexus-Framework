"""
Tenancy — true database-per-tenant isolation, membership-gated.

Each Tenant gets its own physical Postgres database (see `provision_database`
and `nexus.apps.api_infra.tenancy_router`). TenantMiddleware resolves the
tenant for a request from its subdomain or an X-Tenant header, verifies the
caller is a member, and switches the active DB connection for the rest of the
request to that tenant's database. Tenant/Domain/TenantUser themselves stay
in the shared `default` database — see tenancy_router.SHARED_APPS.
"""
from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from nexus.apps.core.validators import alphanumeric_validator
from nexus.apps.api_infra.tenancy_router import (
    register_tenant_database, set_current_tenant_db, reset_current_tenant_db,
)


class Tenant(models.Model):
    """A customer workspace. `schema_name` is kept as a stable slug identifier."""
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True)
    schema_name = models.CharField(max_length=63, unique=True, validators=[alphanumeric_validator])
    is_active = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    plan = models.CharField(max_length=50, default='free')

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    @property
    def db_alias(self):
        return f"tenant_{self.schema_name}"

    @property
    def db_name(self):
        from django.conf import settings
        return f"{settings.DATABASES['default']['NAME']}_tenant_{self.schema_name}"

    def provision_database(self):
        """Create this tenant's physical database (idempotent) and bring it
        to the current schema state.

        This clones `default`'s current schema with pg_dump/psql rather than
        replaying the full migration history on an empty database. Replaying
        history is what a normal `migrate` does, but several early migrations
        in this project predate `db_constraint=False` being added to FKs that
        point at control-plane models (User, ContentType) — those migrations
        briefly create a real `REFERENCES auth_user(...)` constraint that a
        *later* migration then drops. That's fine when `default` already has
        `auth_user`, but a brand new tenant database never gets the shared
        `auth`/`contenttypes` tables (see tenancy_router.SHARED_APPS), so
        replaying that intermediate state fails outright. Cloning the
        already-converged schema sidesteps the problem entirely: it copies
        the *final* DDL, which never references auth_user, and seeds this
        database's migration bookkeeping to match `default`'s, so future
        `migrate_tenants` runs only ever apply new, forward migrations.

        schema_name is alphanumeric-validated, so it's safe to interpolate
        into the CREATE DATABASE identifier.
        """
        import os
        import subprocess

        import psycopg2
        from django.conf import settings
        from django.db import connections
        from django.db.migrations.recorder import MigrationRecorder

        default_cfg = settings.DATABASES['default']
        conn = psycopg2.connect(
            dbname='postgres', user=default_cfg['USER'], password=default_cfg['PASSWORD'],
            host=default_cfg['HOST'], port=default_cfg['PORT'],
        )
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [self.db_name])
                already_existed = cur.fetchone() is not None
                if not already_existed:
                    cur.execute(f'CREATE DATABASE "{self.db_name}"')
        finally:
            conn.close()

        alias = register_tenant_database(self)

        if not already_existed:
            env = {**os.environ, 'PGPASSWORD': default_cfg['PASSWORD']}
            common = ['-h', default_cfg['HOST'], '-p', str(default_cfg['PORT']), '-U', default_cfg['USER']]

            dump = subprocess.run(
                ['pg_dump', '--schema-only', '--no-owner', '--no-privileges', *common, default_cfg['NAME']],
                env=env, capture_output=True, text=True,
            )
            if dump.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {dump.stderr}")

            restore = subprocess.run(
                ['psql', '-v', 'ON_ERROR_STOP=1', *common, self.db_name],
                input=dump.stdout, env=env, capture_output=True, text=True,
            )
            if restore.returncode != 0:
                raise RuntimeError(f"schema restore failed: {restore.stderr}")

            # Seed migration bookkeeping so this database is considered
            # caught up to exactly what `default` has applied right now;
            # future migrations apply incrementally from here on.
            connections[alias].close()
            source_recorder = MigrationRecorder(connections['default'])
            target_recorder = MigrationRecorder(connections[alias])
            target_recorder.ensure_schema()
            for app, name in source_recorder.applied_migrations():
                target_recorder.record_applied(app, name)

        # Catch up on anything applied to `default` after this tenant's
        # database was first cloned - safe now that bookkeeping matches.
        from django.core.management import call_command
        call_command('migrate', database=alias, interactive=False, verbosity=0)

        return alias


class Domain(models.Model):
    """Domain routing for tenants."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=True)

    def __str__(self):
        return self.domain


class TenantUser(models.Model):
    """Link users to tenants with roles."""
    ROLE_CHOICES = [
        ('owner', 'Owner'), ('admin', 'Admin'),
        ('manager', 'Manager'), ('user', 'User'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenants')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['tenant', 'user']

    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name}"


def user_is_member(user, tenant):
    if not (user and user.is_authenticated):
        return False
    if user.is_superuser:
        return True
    return TenantUser.objects.filter(tenant=tenant, user=user, is_active=True).exists()


class TenantViewSet(viewsets.ModelViewSet):
    """Tenant management — admin only."""
    queryset = Tenant.objects.all()
    permission_classes = [IsAdminUser]

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = True
        tenant.save(update_fields=['is_active'])
        return Response({"status": "activated"})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.is_active = False
        tenant.save(update_fields=['is_active'])
        return Response({"status": "deactivated"})

    @action(detail=False, methods=['post'])
    def create_tenant(self, request):
        name = request.data.get('name')
        schema = request.data.get('schema_name')
        if not name or not schema:
            return Response({"error": "name and schema_name required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if Tenant.objects.filter(schema_name=schema).exists():
            return Response({"error": "Schema already exists"},
                            status=status.HTTP_400_BAD_REQUEST)
        tenant = Tenant.objects.create(
            name=name, schema_name=schema, plan=request.data.get('plan', 'free'))
        Domain.objects.create(tenant=tenant, domain=f"{schema}.nexus.local", is_primary=True)

        provisioning_error = None
        try:
            tenant.provision_database()
        except Exception as exc:
            # The Tenant record itself is created either way; the physical
            # database can be (re-)provisioned later via `manage.py
            # migrate_tenants` if this fails (e.g. no CREATEDB privilege).
            provisioning_error = str(exc)

        payload = {"status": "created", "tenant_id": tenant.id, "schema": tenant.schema_name}
        if provisioning_error:
            payload["warning"] = f"Database provisioning failed: {provisioning_error}"
        return Response(payload, status=status.HTTP_201_CREATED)


class TenantUserViewSet(viewsets.ModelViewSet):
    """Tenant membership management."""
    queryset = TenantUser.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A user only sees memberships of tenants they belong to.
        if self.request.user.is_superuser:
            return TenantUser.objects.all()
        my_tenants = TenantUser.objects.filter(
            user=self.request.user, is_active=True).values_list('tenant_id', flat=True)
        return TenantUser.objects.filter(tenant_id__in=my_tenants)

    @action(detail=False, methods=['get'])
    def my_tenants(self, request):
        tenants = TenantUser.objects.filter(user=request.user, is_active=True)
        return Response([{
            "tenant_id": t.tenant.id, "tenant_name": t.tenant.name,
            "role": t.role, "joined_at": t.joined_at,
        } for t in tenants])

    @action(detail=False, methods=['post'])
    def invite(self, request):
        tenant_id = request.data.get('tenant_id')
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'user')
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            user = User.objects.get(id=user_id)
        except Tenant.DoesNotExist:
            return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Only an owner/admin of THIS tenant can invite.
        inviter = TenantUser.objects.filter(
            tenant=tenant, user=request.user, role__in=['owner', 'admin'], is_active=True).first()
        if not (request.user.is_superuser or inviter):
            return Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

        tu, created = TenantUser.objects.get_or_create(
            tenant=tenant, user=user, defaults={'role': role})
        return Response({"status": "invited" if created else "already_member",
                         "user": user.username, "role": role})


class TenantMiddleware:
    """Attach request.tenant from subdomain or X-Tenant header — but ONLY if the
    authenticated caller is a verified member. Never trust the header alone.

    When a tenant is resolved, this also switches the active database
    connection for the rest of the request to that tenant's own database
    (see tenancy_router), and switches it back afterwards."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        host = request.get_host()
        subdomain = host.split('.')[0]
        identifier = request.META.get('HTTP_X_TENANT') or subdomain

        token = None
        if identifier and identifier != 'www':
            try:
                tenant = Tenant.objects.get(schema_name=identifier, is_active=True)
            except Tenant.DoesNotExist:
                tenant = None
            if tenant is not None and user_is_member(getattr(request, 'user', None), tenant):
                request.tenant = tenant
                alias = register_tenant_database(tenant)
                token = set_current_tenant_db(alias)

        try:
            return self.get_response(request)
        finally:
            if token is not None:
                reset_current_tenant_db(token)
