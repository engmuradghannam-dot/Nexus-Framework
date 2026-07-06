from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, TenantUserViewSet

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'tenant-users', TenantUserViewSet, basename='tenant-user')

urlpatterns = [
    path('', include(router.urls)),
]
