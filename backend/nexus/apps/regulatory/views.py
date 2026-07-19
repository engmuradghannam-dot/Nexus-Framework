from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Regulation, ComplianceCheck
from nexus.apps.core.models import Branch
from .serializers import RegulationSerializer, ComplianceCheckSerializer

class RegulationViewSet(viewsets.ModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer
    permission_classes = [IsAuthenticated]


    @action(detail=True, methods=['get'])
    def compliance_score(self, request, pk=None):
        regulation = self.get_object()
        checks = regulation.checks.all()
        total = checks.count()
        passed = checks.filter(result='pass').count()
        score = (passed / total * 100) if total else 0
        return Response({
            "regulation": regulation.title,
            "total_checks": total,
            "passed": passed,
            "failed": checks.filter(result='fail').count(),
            "pending": checks.filter(result='pending').count(),
            "score": round(score, 2)
        })

    @action(detail=True, methods=['post'])
    def auto_check(self, request, pk=None):
        regulation = self.get_object()
        # Simulate automated compliance check
        from random import choice
        branches = Branch.objects.all()
        results = []
        for branch in branches:
            result = choice(['pass', 'pass', 'pass', 'fail', 'pending'])
            check, _ = ComplianceCheck.objects.get_or_create(
                regulation=regulation,
                branch=branch,
                defaults={'result': result, 'checked_by': request.user}
            )
            check.result = result
            check.save()
            results.append({"branch": branch.name, "result": result})
        return Response({"status": "checks completed", "results": results})

    @action(detail=False, methods=['get'])
    def expiry_alerts(self, request):
        from datetime import date, timedelta
        upcoming = date.today() + timedelta(days=30)
        regulations = Regulation.objects.filter(expiry_date__lte=upcoming, expiry_date__gte=date.today())
        serializer = self.get_serializer(regulations, many=True)
        return Response({"count": regulations.count(), "regulations": serializer.data})


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
