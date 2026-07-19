from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet, UserRoleViewSet, FieldPermissionViewSet,
    RecordPermissionViewSet, PermissionAuditViewSet
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'user-roles', UserRoleViewSet)
router.register(r'field-permissions', FieldPermissionViewSet)
router.register(r'record-permissions', RecordPermissionViewSet)
router.register(r'audit', PermissionAuditViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
