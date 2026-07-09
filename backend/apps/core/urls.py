from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    UserViewSet, CompanyProfileViewSet,
    BranchViewSet, WarehouseViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyProfileViewSet, basename='company')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', obtain_auth_token, name='api_token_auth'),
]
