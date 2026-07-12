from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RoleAssignmentViewSet, RoleViewSet

router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"assignments", RoleAssignmentViewSet, basename="role-assignment")

urlpatterns = [path("", include(router.urls))]
