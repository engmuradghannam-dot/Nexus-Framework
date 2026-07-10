"""Reusable DRF view mixins for the Nexus Framework.

* ``CompanyScopedMixin`` enforces multi-tenant isolation so a user can only
  read/write rows belonging to a company they manage (prevents IDOR).
* ``LockAfterSubmitMixin`` prevents editing child rows once their parent
  document has moved out of an editable (Draft) status.
"""

from rest_framework.exceptions import PermissionDenied


class CompanyScopedMixin:
    """Restrict a ``ModelViewSet`` queryset to the requesting user's companies.

    Configure ``company_field`` on the viewset with the (possibly nested)
    lookup path that reaches the owning company, e.g. ``'company'`` or
    ``'sales_order__company'``. Superusers bypass scoping. Anonymous or
    company-less users get an empty queryset (fail closed).
    """

    company_field = "company"

    def _user_companies(self):
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return user.managed_companies.all()

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if getattr(user, "is_superuser", False):
            return qs
        companies = self._user_companies()
        if not companies:
            return qs.none()
        return qs.filter(**{f"{self.company_field}__in": companies})

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        # Auto-assign the company for direct-company models when the caller
        # omitted it and manages exactly one company.
        if (
            self.company_field == "company"
            and "company" not in serializer.validated_data
            and not getattr(user, "is_superuser", False)
        ):
            companies = self._user_companies()
            if companies is not None and companies.count() == 1:
                serializer.save(company=companies.first())
                return
        serializer.save()


class LockAfterSubmitMixin:
    """Block writes to child rows once the parent document leaves 'Draft'.

    Set ``parent_field`` to the FK attribute pointing at the parent document
    (which must expose a ``status``). Applies to update, partial update and
    destroy operations.
    """

    parent_field = None
    editable_statuses = ("Draft",)

    def _assert_parent_editable(self, instance):
        if not self.parent_field:
            return
        parent = getattr(instance, self.parent_field, None)
        status = getattr(parent, "status", None)
        if status is not None and status not in self.editable_statuses:
            raise PermissionDenied(
                f"Cannot modify: parent document is '{status}' (locked)."
            )

    def perform_update(self, serializer):
        self._assert_parent_editable(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_parent_editable(instance)
        instance.delete()
