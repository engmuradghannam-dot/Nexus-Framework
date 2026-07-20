from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from nexus.apps.api_infra.scoping import CompanyScopedViewSet, user_company_ids
from .models import Company, Branch, Warehouse, SubWarehouse, Department, HRProfile
from .serializers import (
    CompanySerializer, BranchSerializer, WarehouseSerializer,
    SubWarehouseSerializer, DepartmentSerializer, HRProfileSerializer, UserSerializer
)


def _user_payload(user):
    return {
        'authenticated': True,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


@method_decorator(ensure_csrf_cookie, name='get')
class SessionView(APIView):
    """SPA session auth: GET reports whether the caller is logged in (and,
    as a side effect, sets the csrftoken cookie so a subsequent POST here
    can carry a valid X-CSRFToken - there's no server-rendered form for the
    browser to pick that cookie up from otherwise). POST logs in, DELETE
    logs out."""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'authenticated': False})
        return Response(_user_payload(request.user))

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'username and password are required'},
                             status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response(_user_payload(user))

    def delete(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyViewSet(CompanyScopedViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    company_field = "id"   # the Company IS the scope key

    def get_permissions(self):
        # CompanyScopedPermission only checks membership on existing objects
        # (has_object_permission, never called for create) - creating a new
        # top-level Company is the one action here that isn't scoped by
        # anything, so it needs its own explicit gate rather than falling
        # through to "any authenticated user".
        if self.action == 'create':
            return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # CompanyScopedViewSet.perform_create() assumes the model being
        # created has a `company` FK to read from validated_data - Company
        # itself doesn't (it IS the scope key, via company_field="id"
        # above), so that inherited logic always raised "company is
        # required" here. A new company isn't scoped by an existing one.
        serializer.save()

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        companies = self.get_queryset().filter(
            Q(name__icontains=query) | Q(description__icontains=query) |
            Q(address__icontains=query))
        return Response(self.get_serializer(companies, many=True).data)

    @action(detail=False, methods=['post'])
    def export_csv(self, request):
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="companies.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Description', 'Address', 'Created'])
        for c in self.get_queryset():
            writer.writerow([c.id, c.name, c.description, c.address, c.created_at])
        return response

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        ids = request.data.get('ids', [])
        deleted = self.get_queryset().filter(id__in=ids).delete()
        return Response({"deleted": deleted[0]})


class BranchViewSet(CompanyScopedViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    company_field = "company"

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)


class WarehouseViewSet(CompanyScopedViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    company_field = "branch__company"

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if not branch_id:
            return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)
        warehouses = self.get_queryset().filter(branch_id=branch_id)
        return Response(self.get_serializer(warehouses, many=True).data)


class SubWarehouseViewSet(CompanyScopedViewSet):
    queryset = SubWarehouse.objects.all()
    serializer_class = SubWarehouseSerializer
    company_field = "warehouse__branch__company"

    @action(detail=False, methods=['get'])
    def by_warehouse(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if not warehouse_id:
            return Response({"error": "warehouse_id required"}, status=status.HTTP_400_BAD_REQUEST)
        subs = self.get_queryset().filter(warehouse_id=warehouse_id)
        return Response(self.get_serializer(subs, many=True).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """Shared lookup — no company FK on the model."""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class HRProfileViewSet(CompanyScopedViewSet):
    queryset = HRProfile.objects.all()
    serializer_class = HRProfileSerializer
    company_field = "branch__company"

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = HRProfile.objects.get(user=request.user)
        except HRProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(profile).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def update_permissions(self, request):
        user_id = request.data.get('user_id')
        permissions = request.data.get('permissions', {})
        try:
            profile = HRProfile.objects.get(user_id=user_id)
        except HRProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        profile.permissions = permissions
        profile.save(update_fields=['permissions'])
        return Response({"status": "permissions updated"})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return User.objects.all()
        allowed = user_company_ids(user)
        if not allowed:
            return User.objects.filter(id=user.id)
        return User.objects.filter(
            hr_profile__branch__company_id__in=allowed).distinct() | User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def current(self, request):
        return Response(self.get_serializer(request.user).data)
