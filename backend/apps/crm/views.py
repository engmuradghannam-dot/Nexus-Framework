from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets

from apps.core.mixins import CompanyScopedMixin

from .models import LeadScoringRule, Lead, Opportunity
from .serializers import LeadScoringRuleSerializer, LeadSerializer, OpportunitySerializer


class LeadViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    company_field = "company"


    @action(detail=True, methods=["post"])
    def rescore(self, request, pk=None):
        """CRM-RULE-001: recompute from the rules Sales configured, and show
        which ones fired — a score nobody can explain is a number nobody
        should act on."""
        lead = self.get_object()
        score = lead.recalculate_score()
        return Response({"score": score, "breakdown": lead.score_breakdown()})

class OpportunityViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    company_field = "company"


class LeadScoringRuleViewSet(CompanyScopedMixin, viewsets.ModelViewSet):
    """CRM-RULE-001: Sales enters the signals and weights here."""

    queryset = LeadScoringRule.objects.select_related("company")
    serializer_class = LeadScoringRuleSerializer
    company_field = "company"
