from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "permissions_level", "department"]
    search_fields = ["email", "username", "first_name", "last_name"]

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Return the currently authenticated user."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CompanyProfileViewSet(viewsets.ModelViewSet):
    """
    Company Profile - the ROOT entity controlled by Industry Vertical.
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


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related("company", "manager").prefetch_related(
        "warehouses"
    )
    serializer_class = BranchSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["company", "is_active"]
    search_fields = ["name", "code", "address"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.select_related(
        "branch", "parent_warehouse"
    ).prefetch_related("sub_warehouses")
    serializer_class = WarehouseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["branch", "is_active"]
    search_fields = ["name", "code"]
