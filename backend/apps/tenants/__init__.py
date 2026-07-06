"""
Tenants app for SaaS multi-tenancy.
Provides schema-per-tenant isolation with PostgreSQL.
"""
default_app_config = 'apps.tenants.apps.TenantsConfig'
