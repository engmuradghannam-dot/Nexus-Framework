"""Reusable DRF view mixins for the Nexus Framework.

* ``CompanyScopedMixin`` enforces multi-tenant isolation so a user can only
  read/write rows belonging to a company they manage (prevents IDOR).
* ``LockAfterSubmitMixin`` prevents editing child rows once their parent
  document has moved out of an editable (Draft) status.
"""

from rest_framework.exceptions import PermissionDenied, ValidationError


class CompanyScopedMixin:
    """Restrict a ``ModelViewSet`` queryset to the requesting user's companies.

    Configure ``company_field`` on the viewset with the (possibly nested)
    lookup path that reaches the owning company, e.g. ``'company'`` or
    ``'sales_order__company'``. Superusers bypass scoping. Anonymous or
    company-less users get an empty queryset (fail closed).

    For direct-company models (``company_field == "company"``), ``company``
    is also made optional on write: the serializer field is relaxed to
    non-required (see ``get_serializer``) so callers who manage exactly one
    company — or, for superusers, installations with exactly one company
    overall — don't have to re-select it on every request. ``perform_create``
    still enforces that a company is resolvable, just later and with a
    proper 400 instead of DRF's generic "this field is required" (which
    would otherwise fire before this auto-assignment logic ever runs).
    """

    company_field = "company"

    def _user_companies(self):
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return None
        return user.managed_companies.all()

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if self.company_field == "company":
            # list/many=True calls return a ListSerializer, which has no
            # top-level `fields` of its own (its `.child` does) — nothing to
            # relax there since it's never used for writes.
            company_field = getattr(serializer, "fields", {}).get("company")
            if company_field is not None:
                company_field.required = False
        return serializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if getattr(user, "is_superuser", False):
            return qs
        companies = self._user_companies()
        if not companies:
            return qs.none()
        return qs.filter(**{f"{self.company_field}__in": companies})

    def _resolve_company(self):
        """Pick an implicit company for the current user, or None if it
        can't be inferred unambiguously."""
        from apps.core.models import CompanyProfile

        user = getattr(self.request, "user", None)
        if getattr(user, "is_superuser", False):
            qs = CompanyProfile.objects.all()
            return qs.first() if qs.count() == 1 else None
        companies = self._user_companies()
        if companies is not None and companies.count() == 1:
            return companies.first()
        return None

    def perform_create(self, serializer):
        if self.company_field == "company" and "company" not in serializer.validated_data:
            company = self._resolve_company()
            if company is None:
                raise ValidationError(
                    {"company": "This field is required (couldn't be inferred automatically — more than one company exists)."}
                )
            serializer.save(company=company)
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
