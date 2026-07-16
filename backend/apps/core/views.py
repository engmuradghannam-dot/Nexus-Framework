from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.views.decorators.csrf import ensure_csrf_cookie
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser
from rest_framework.response import Response

from apps.core.mixins import CompanyScopedMixin
from apps.tenants.mixins import TenantScopedMixin

from .models import Branch, CompanyProfile, User, Warehouse
from .serializers import (
    BranchSerializer,
    CompanyProfileListSerializer,
    CompanyProfileSerializer,
    UserSerializer,
    WarehouseSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """Self-service account creation: email + password (+ optional name).
    Logs the new user in immediately, same response shape as login_view."""
    email = (request.data.get("email") or "").strip()
    password = request.data.get("password") or ""
    first_name = (request.data.get("first_name") or "").strip()
    last_name = (request.data.get("last_name") or "").strip()

    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_email(email)
    except DjangoValidationError:
        return Response(
            {"detail": "Enter a valid email address."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(password) < 8:
        return Response(
            {"detail": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if User.objects.filter(email__iexact=email).exists():
        return Response(
            {"detail": "An account with this email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        email=email, password=password, first_name=first_name, last_name=last_name
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_view(request):
    """Issue the csrftoken cookie for session-authenticated (non-Token) API access."""
    return Response({"detail": "CSRF cookie set."})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """Authenticate by email + password and return a token and the user."""
    email = request.data.get("email")
    password = request.data.get("password")
    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Resolve the stored email case-insensitively so any casing works.
    existing = User.objects.filter(email__iexact=email).first()
    lookup_email = existing.email if existing else email
    user = authenticate(request, username=lookup_email, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


class IsSelfOrSuperuser(BasePermission):
    """Object-level guard: only a user themselves, or a superuser, may
    retrieve/update/delete a specific User row."""

    def has_object_permission(self, request, view, obj):
        return bool(
            getattr(request.user, "is_superuser", False) or obj.pk == request.user.pk
        )


class UserViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "permissions_level", "department"]
    search_fields = ["email", "username", "first_name", "last_name"]

    def get_permissions(self):
        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return [p() for p in self.permission_classes] + [IsSelfOrSuperuser()]
        return super().get_permissions()

    def get_queryset(self):
        # A user can always see/edit their own row via this endpoint even
        # when tenant-less (the default right after self-registration) —
        # TenantScopedMixin would otherwise fail-close them out of it.
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_authenticated", False):
            return qs | User.objects.filter(pk=user.pk)
        return qs

    def get_serializer(self, *args, **kwargs):
        """permissions_level/is_active are role/account-state, not
        self-service profile fields — only a superuser may change them, so
        they're read-only for anyone else (blocks self-escalation and
        deactivating other users)."""
        serializer = super().get_serializer(*args, **kwargs)
        if not getattr(self.request.user, "is_superuser", False):
            for name in ("permissions_level", "is_active"):
                field = serializer.fields.get(name)
                if field is not None:
                    field.read_only = True
        return serializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Return the currently authenticated user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CompanyProfileViewSet(viewsets.ModelViewSet):
    """
    Company Profile - the ROOT entity controlled by Industry Vertical.

    This is the model ``CompanyScopedMixin`` scopes every other company-owned
    ViewSet *by* (via ``user.managed_companies``, the reverse of
    ``super_admin``), so it can't use that mixin on itself. Instead: non-superusers
    only see companies they already manage, and only superusers may create,
    edit, or reassign ``super_admin`` on a company at all — otherwise any
    authenticated user could PATCH themselves onto ``super_admin`` and
    inherit full access to that company's data everywhere else in the app.
    """

    queryset = CompanyProfile.objects.select_related(
        "industry_vertical"
    ).prefetch_related("branches")
    serializer_class = CompanyProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "industry_vertical", "multi_branch_enabled"]
    search_fields = ["name", "code"]

    def get_serializer_class(self):
        if self.action == "list":
            return CompanyProfileListSerializer
        return CompanyProfileSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return qs
        return qs.filter(id__in=user.managed_companies.all())

    @action(detail=True, methods=["get"])
    def modules(self, request, pk=None):
        """Get effective modules for this company"""
        company = self.get_object()
        return Response(
            {
                "company": company.name,
                "vertical": company.industry_vertical.name,
                "effective_modules": company.effective_modules,
                "effective_features": company.effective_features,
            }
        )

    @action(detail=True, methods=["get"])
    def branches(self, request, pk=None):
        """Get branches for this company"""
        company = self.get_object()
        branches = company.branches.all()
        serializer = BranchSerializer(branches, many=True)
        return Response(
            {
                "company": company.name,
                "count": branches.count(),
                "branches": serializer.data,
            }
        )


class BranchViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.select_related("company", "manager").prefetch_related(
        "warehouses"
    )
    serializer_class = BranchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["company", "is_active"]
    search_fields = ["name", "code", "address"]
    company_field = "company"


class WarehouseViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Warehouse.objects.select_related(
        "branch", "parent_warehouse"
    ).prefetch_related("sub_warehouses")
    serializer_class = WarehouseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["branch", "is_active"]
    search_fields = ["name", "code"]
    company_field = "branch__company"
