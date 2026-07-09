from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, EmployeeViewSet, TeamViewSet, LeaveRequestViewSet, PayrollViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'payrolls', PayrollViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
