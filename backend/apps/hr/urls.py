from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (  # noqa: F401
    EmployeeTerminationViewSet,
    EndOfServiceBandViewSet,
    EndOfServicePolicyViewSet,
    HRPolicyViewSet,
    LeaveEntitlementViewSet,
)
from .views import (
    DepartmentViewSet,
    EmployeeViewSet,
    LeaveRequestViewSet,
    PayrollViewSet,
    TeamViewSet,
)

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet)
router.register(r"employees", EmployeeViewSet)
router.register(r"terminations", EmployeeTerminationViewSet)
router.register(r"hr-policies", HRPolicyViewSet)
router.register(r"leave-entitlements", LeaveEntitlementViewSet)
router.register(r"eosb-policies", EndOfServicePolicyViewSet)
router.register(r"eosb-bands", EndOfServiceBandViewSet)
router.register(r"teams", TeamViewSet)
router.register(r"leave-requests", LeaveRequestViewSet)
router.register(r"payrolls", PayrollViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
