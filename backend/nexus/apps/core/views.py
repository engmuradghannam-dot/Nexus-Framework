from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import Company, Branch, Warehouse, SubWarehouse, Department, HRProfile
from .serializers import (
    CompanySerializer, BranchSerializer, WarehouseSerializer,
    SubWarehouseSerializer, DepartmentSerializer, HRProfileSerializer, UserSerializer
)

class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_company(self, request):
        company_id = request.query_params.get('company_id')
        if company_id:
            branches = Branch.objects.filter(company_id=company_id)
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data)
        return Response({"error": "company_id required"}, status=status.HTTP_400_BAD_REQUEST)

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            warehouses = Warehouse.objects.filter(branch_id=branch_id)
            serializer = self.get_serializer(warehouses, many=True)
            return Response(serializer.data)
        return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)

class SubWarehouseViewSet(viewsets.ModelViewSet):
    queryset = SubWarehouse.objects.all()
    serializer_class = SubWarehouseSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_warehouse(self, request):
        warehouse_id = request.query_params.get('warehouse_id')
        if warehouse_id:
            sub_warehouses = SubWarehouse.objects.filter(warehouse_id=warehouse_id)
            serializer = self.get_serializer(sub_warehouses, many=True)
            return Response(serializer.data)
        return Response({"error": "warehouse_id required"}, status=status.HTTP_400_BAD_REQUEST)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

class HRProfileViewSet(viewsets.ModelViewSet):
    queryset = HRProfile.objects.all()
    serializer_class = HRProfileSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = HRProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except HRProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def update_permissions(self, request):
        user_id = request.data.get('user_id')
        permissions = request.data.get('permissions', {})
        try:
            profile = HRProfile.objects.get(user_id=user_id)
            profile.permissions = permissions
            profile.save()
            return Response({"status": "permissions updated"})
        except HRProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
