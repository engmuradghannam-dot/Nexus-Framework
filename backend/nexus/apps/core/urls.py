from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, BranchViewSet, WarehouseViewSet,
    SubWarehouseViewSet, DepartmentViewSet, HRProfileViewSet, UserViewSet,
    SessionView,
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
    path('session/', SessionView.as_view(), name='session'),
    path('', include(router.urls)),
]
