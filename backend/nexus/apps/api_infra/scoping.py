"""
Company-level access scoping — the single choke point that fixes the
cross-tenant IDOR.

Root cause it replaces: viewsets filtered by a client-supplied
`company_id` query param (or fell back to `.objects.all()`) with no check
that the user belongs to that company. Any authenticated user could read
any company's data.

Rule enforced here: the set of companies a user may touch is derived from
the SERVER SIDE (their identity), never from the request. A client-supplied
company_id is only ever validated against that set, never trusted.

NOTE on the membership source: this codebase links a user to a company only
through `user.hr_profile.branch.company`. That is what `user_company_ids`
uses. If you introduce an explicit membership model (recommended), point
this one function at it and every viewset inherits the fix.
"""
from rest_framework import viewsets, permissions, exceptions


def user_company_ids(user):
    """Return the set of company ids the user may access, or None for
    'all companies' (superuser/staff). Empty set => access nothing."""
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser or user.is_staff:
        return None  # unrestricted
    ids = set()
    profile = getattr(user, "hr_profile", None)
    branch = getattr(profile, "branch", None) if profile else None
    if branch and branch.company_id:
        ids.add(branch.company_id)
    # Extend here if a user can belong to multiple companies.
    return ids


class CompanyScopedPermission(permissions.IsAuthenticated):
    """Authenticated + object must belong to one of the user's companies."""

    def has_object_permission(self, request, view, obj):
        allowed = user_company_ids(request.user)
        if allowed is None:
            return True
        company_id = getattr(obj, "company_id", None)
        if company_id is None:
            # object reached via a relation (e.g. line -> entry -> company)
            company_id = view.resolve_company_id(obj)
        return company_id in allowed


class CompanyScopedViewSet(viewsets.ModelViewSet):
    """Base viewset that confines every read/write to the caller's companies.

    Subclasses set `company_field` if the model reaches Company through a
    relation (e.g. 'journal_entry__company'). Direct `company` FK is the
    default.
    """
    permission_classes = [CompanyScopedPermission]
    company_field = "company"

    # --- queryset scoping ---
    def get_queryset(self):
        qs = super().get_queryset()
        return self.scope(qs)

    def scope(self, qs):
        allowed = user_company_ids(self.request.user)
        if allowed is None:
            return qs
        if not allowed:
            return qs.none()
        return qs.filter(**{f"{self.company_field}__in": allowed})

    def resolve_company_id(self, obj):
        """Walk `company_field` (supports '__' relations) to the company id."""
        cur = obj
        for part in self.company_field.split("__"):
            cur = getattr(cur, part, None)
            if cur is None:
                return None
        return getattr(cur, "id", cur)

    # --- safe company selection on write ---
    def require_company(self, requested_id=None):
        """Return a company id the user is allowed to write to, or raise.
        Used by create/custom actions instead of trusting request input."""
        allowed = user_company_ids(self.request.user)
        if allowed is None:
            if requested_id is None:
                raise exceptions.ValidationError("company is required")
            return requested_id
        if not allowed:
            raise exceptions.PermissionDenied("user is not attached to any company")
        if requested_id is None:
            if len(allowed) == 1:
                return next(iter(allowed))
            raise exceptions.ValidationError("company is required (user has several)")
        if requested_id not in allowed:
            raise exceptions.PermissionDenied("not a member of that company")
        return requested_id

    def perform_create(self, serializer):
        requested = serializer.validated_data.get("company")
        requested_id = getattr(requested, "id", requested)
        company_id = self.require_company(requested_id)
        serializer.save(**({} if requested is not None and getattr(requested, "id", None)
                           else {"company_id": company_id}))
