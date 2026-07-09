from rest_framework import viewsets, permissions
from .models import IndustryProject, IndustryMetric
from .serializers import IndustryProjectSerializer, IndustryMetricSerializer


class IndustryProjectViewSet(viewsets.ModelViewSet):
    queryset = IndustryProject.objects.all()
    serializer_class = IndustryProjectSerializer
    permission_classes = [permissions.IsAuthenticated]


class IndustryMetricViewSet(viewsets.ModelViewSet):
    queryset = IndustryMetric.objects.all()
    serializer_class = IndustryMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
