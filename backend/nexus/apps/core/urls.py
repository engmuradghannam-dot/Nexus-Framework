from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, BranchViewSet, WarehouseViewSet,
    SubWarehouseViewSet, DepartmentViewSet, HRProfileViewSet, UserViewSet
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'sub-warehouses', SubWarehouseViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'hr-profiles', HRProfileViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
