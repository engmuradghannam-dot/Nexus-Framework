"""
Tenant-aware file storage backend.
Isolates files per tenant using S3 prefixes.
"""
import os
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class TenantStorageMixin:
    """Mixin to add tenant isolation to any storage backend."""

    def _get_tenant_prefix(self):
        """Get tenant-specific prefix from thread-local or request."""
        from apps.core.threadlocal import get_current_tenant
        tenant = get_current_tenant()
        if tenant:
            return f"tenants/{tenant.get('schema_name', 'unknown')}/"
        return "public/"

    def _save(self, name, content):
        prefix = self._get_tenant_prefix()
        name = os.path.join(prefix, name)
        return super()._save(name, content)

    def _open(self, name, mode='rb'):
        prefix = self._get_tenant_prefix()
        name = os.path.join(prefix, name)
        return super()._open(name, mode)

    def exists(self, name):
        prefix = self._get_tenant_prefix()
        name = os.path.join(prefix, name)
        return super().exists(name)

    def delete(self, name):
        prefix = self._get_tenant_prefix()
        name = os.path.join(prefix, name)
        return super().delete(name)

    def url(self, name):
        prefix = self._get_tenant_prefix()
        name = os.path.join(prefix, name)
        return super().url(name)


class TenantFileSystemStorage(TenantStorageMixin, FileSystemStorage):
    """Tenant-aware local file storage."""
    pass


class TenantS3Storage(TenantStorageMixin, S3Boto3Storage):
    """Tenant-aware S3 storage."""

    def __init__(self, *args, **kwargs):
        kwargs['location'] = kwargs.get('location', '')
        super().__init__(*args, **kwargs)


# Default storage based on settings
if getattr(settings, 'DEFAULT_FILE_STORAGE', '').endswith('S3Boto3Storage'):
    TenantStorage = TenantS3Storage
else:
    TenantStorage = TenantFileSystemStorage
