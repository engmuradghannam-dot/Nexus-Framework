from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BranchViewSet,
    CompanyProfileViewSet,
    UserViewSet,
    WarehouseViewSet,
    login_view,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"companies", CompanyProfileViewSet, basename="company")
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", login_view, name="api_login"),
]
