from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Regulation, ComplianceCheck
from .serializers import RegulationSerializer, ComplianceCheckSerializer

class RegulationViewSet(viewsets.ModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer
    permission_classes = [IsAuthenticated]

class ComplianceCheckViewSet(viewsets.ModelViewSet):
    queryset = ComplianceCheck.objects.all()
    serializer_class = ComplianceCheckSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def by_branch(self, request):
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            checks = ComplianceCheck.objects.filter(branch_id=branch_id)
            serializer = self.get_serializer(checks, many=True)
            return Response(serializer.data)
        return Response({"error": "branch_id required"}, status=status.HTTP_400_BAD_REQUEST)
