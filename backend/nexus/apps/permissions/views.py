from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Role, UserRole, FieldPermission, RecordPermission, PermissionAudit
from .serializers import (
    RoleSerializer, UserRoleSerializer, FieldPermissionSerializer,
    RecordPermissionSerializer, PermissionAuditSerializer
)

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        role = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        role.django_permissions.set(permission_ids)
        return Response({"status": "permissions updated"})

class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            roles = UserRole.objects.filter(user_id=user_id)
            serializer = self.get_serializer(roles, many=True)
            return Response(serializer.data)
        return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)

class FieldPermissionViewSet(viewsets.ModelViewSet):
    queryset = FieldPermission.objects.all()
    serializer_class = FieldPermissionSerializer
    permission_classes = [IsAdminUser]

class RecordPermissionViewSet(viewsets.ModelViewSet):
    queryset = RecordPermission.objects.all()
    serializer_class = RecordPermissionSerializer
    permission_classes = [IsAdminUser]

class PermissionAuditViewSet(viewsets.ModelViewSet):
    queryset = PermissionAudit.objects.all()
    serializer_class = PermissionAuditSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            audits = PermissionAudit.objects.filter(user_id=user_id)
            serializer = self.get_serializer(audits, many=True)
            return Response(serializer.data)
        return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)
