from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Branch, CompanyProfile, User, Warehouse
from .serializers import (
    BranchSerializer,
    CompanyProfileListSerializer,
    CompanyProfileSerializer,
    UserSerializer,
    WarehouseSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["is_active", "permissions_level", "department"]
    search_fields = ["email", "username", "first_name", "last_name"]


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
