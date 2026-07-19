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


    @action(detail=False, methods=['post'])
    def check_permission(self, request):
        user_id = request.data.get('user_id')
        action = request.data.get('action')
        resource = request.data.get('resource')

        if not all([user_id, action, resource]):
            return Response({"error": "user_id, action, resource required"}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
            has_perm = user.has_perm(f'{action}_{resource}')
            return Response({
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "has_permission": has_perm
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def impersonate(self, request):
        target_user_id = request.data.get('user_id')
        if target_user_id:
            from django.contrib.auth.models import User
            try:
                target = User.objects.get(id=target_user_id)
                # Log the impersonation
                PermissionAudit.objects.create(
                    user=request.user,
                    action='impersonate',
                    resource_type='user',
                    resource_id=target.id,
                    details={'impersonated_user': target.username},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return Response({
                    "status": "impersonating",
                    "target_user": target.username,
                    "target_id": target.id,
                    "note": "Set session user to target for impersonation"
                })
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "user_id required"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def session_list(self, request):
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        sessions = Session.objects.filter(expire_date__gt=timezone.now())
        data = []
        for session in sessions:
            data.append({
                "session_key": session.session_key[:8] + "...",
                "expire_date": session.expire_date,
                "has_data": bool(session.get_decoded())
            })
        return Response({"active_sessions": len(data), "sessions": data})

    @action(detail=False, methods=['get'])
    def rate_limit(self, request):
        from django.core.cache import cache
        user_id = request.user.id
        key = f"rate_limit_{user_id}"
        current = cache.get(key, 0)
        limit = 100  # requests per minute
        remaining = max(0, limit - current)
        return Response({
            "limit": limit,
            "remaining": remaining,
            "used": current,
            "reset_in": 60
        })


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
