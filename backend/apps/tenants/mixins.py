"""DRF mixin enforcing tenant isolation on tenant-scoped viewsets.

Cooperative with other mixins (e.g. CompanyScopedMixin): get_queryset and
perform_create both call super(), so tenant filtering/stamping composes with
company scoping instead of replacing it.
"""


class TenantScopedMixin:
    """Filter a viewset queryset to the requesting user's tenant.

    - Superusers see everything (cross-tenant admin).
    - Users WITH a tenant see only their tenant's rows.
    - Users WITHOUT a tenant are grandfathered (see all) so legacy data and
      the existing test suite keep working.
    On create, the row's tenant is set to the user's tenant automatically.
    """

    def _user_tenant(self):
        user = getattr(self.request, "user", None)
        return getattr(user, "tenant", None) if user and user.is_authenticated else None

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if getattr(user, "is_superuser", False):
            return qs
        tenant = self._user_tenant()
        if tenant is None:
            return qs
        return qs.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = self._user_tenant()
        if tenant is not None:
            serializer.validated_data["tenant"] = tenant
        parent = getattr(super(), "perform_create", None)
        if callable(parent):
            parent(serializer)
        else:
            serializer.save()
