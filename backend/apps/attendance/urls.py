from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet, TimesheetViewSet

router = DefaultRouter()
router.register(r"attendance", AttendanceViewSet, basename="attendance")
router.register(r"timesheets", TimesheetViewSet, basename="timesheet")

urlpatterns = [path("", include(router.urls))]
