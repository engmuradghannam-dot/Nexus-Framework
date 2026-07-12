from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import Attendance, Timesheet
from .serializers import AttendanceSerializer, TimesheetSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "date", "employee_no"]


class TimesheetViewSet(viewsets.ModelViewSet):
    queryset = Timesheet.objects.all()
    serializer_class = TimesheetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["date", "billable"]
