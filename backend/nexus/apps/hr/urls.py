from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, AttendanceViewSet, LeaveTypeViewSet,
    LeaveRequestViewSet, SalaryStructureViewSet, EmployeeSalaryViewSet,
    PayrollRunViewSet, PayslipViewSet
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'leave-types', LeaveTypeViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'salary-structures', SalaryStructureViewSet)
router.register(r'employee-salaries', EmployeeSalaryViewSet)
router.register(r'payroll-runs', PayrollRunViewSet)
router.register(r'payslips', PayslipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
