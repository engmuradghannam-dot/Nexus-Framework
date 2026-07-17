from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BinLocationViewSet,
    BranchViewSet,
    CompanyProfileViewSet,
    UserViewSet,
    WarehouseViewSet,
    csrf_view,
    login_view,
    register_view,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"companies", CompanyProfileViewSet, basename="company")
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"bin-locations", BinLocationViewSet, basename="bin-location")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/csrf/", csrf_view, name="api_csrf"),
    path("auth/login/", login_view, name="api_login"),
    path("auth/register/", register_view, name="api_register"),
]
