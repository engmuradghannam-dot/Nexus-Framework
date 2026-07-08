"""PMO Views"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    ProjectCharter, BusinessCase, Stakeholder, Requirement, WBS,
    Deliverable, Milestone, Sprint, KanbanBoard, KanbanCard,
    Resource, RACI, Risk, Issue, ChangeRequest, DecisionLog,
    QualityPlan, QAChecklist, TestCase, Bug, UATSession,
    WeeklyReport, MonthlyReport, LessonsLearned, MeetingMinutes,
    ActionItem, Dependency, CommunicationPlan, DocumentRegister,
    TrainingPlan, GoLiveChecklist, MaintenancePlan, ProjectClosure
)
from .serializers import (
    ProjectCharterSerializer, BusinessCaseSerializer, StakeholderSerializer,
    RequirementSerializer, WBSSerializer, DeliverableSerializer,
    MilestoneSerializer, SprintSerializer, KanbanBoardSerializer,
    KanbanCardSerializer, ResourceSerializer, RACISerializer,
    RiskSerializer, IssueSerializer, ChangeRequestSerializer,
    DecisionLogSerializer, QualityPlanSerializer, QAChecklistSerializer,
    TestCaseSerializer, BugSerializer, UATSessionSerializer,
    WeeklyReportSerializer, MonthlyReportSerializer, LessonsLearnedSerializer,
    MeetingMinutesSerializer, ActionItemSerializer, DependencySerializer,
    CommunicationPlanSerializer, DocumentRegisterSerializer,
    TrainingPlanSerializer, GoLiveChecklistSerializer,
    MaintenancePlanSerializer, ProjectClosureSerializer
)

class ProjectCharterViewSet(viewsets.ModelViewSet):
    queryset = ProjectCharter.objects.all()
    serializer_class = ProjectCharterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'company']
    search_fields = ['project_name', 'project_code', 'description']
    ordering_fields = ['start_date', 'priority', 'progress']

class BusinessCaseViewSet(viewsets.ModelViewSet):
    queryset = BusinessCase.objects.all()
    serializer_class = BusinessCaseSerializer

class StakeholderViewSet(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer

class RequirementViewSet(viewsets.ModelViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'priority', 'req_type']
    search_fields = ['title', 'description']

class WBSViewSet(viewsets.ModelViewSet):
    queryset = WBS.objects.all()
    serializer_class = WBSSerializer

class DeliverableViewSet(viewsets.ModelViewSet):
    queryset = Deliverable.objects.all()
    serializer_class = DeliverableSerializer

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer

class SprintViewSet(viewsets.ModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer

class KanbanBoardViewSet(viewsets.ModelViewSet):
    queryset = KanbanBoard.objects.all()
    serializer_class = KanbanBoardSerializer

class KanbanCardViewSet(viewsets.ModelViewSet):
    queryset = KanbanCard.objects.all()
    serializer_class = KanbanCardSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['board', 'column', 'priority']

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer

class RACIViewSet(viewsets.ModelViewSet):
    queryset = RACI.objects.all()
    serializer_class = RACISerializer

class RiskViewSet(viewsets.ModelViewSet):
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'category', 'probability', 'impact']
    search_fields = ['title', 'description']

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer

class ChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all()
    serializer_class = ChangeRequestSerializer

class DecisionLogViewSet(viewsets.ModelViewSet):
    queryset = DecisionLog.objects.all()
    serializer_class = DecisionLogSerializer

class QualityPlanViewSet(viewsets.ModelViewSet):
    queryset = QualityPlan.objects.all()
    serializer_class = QualityPlanSerializer

class QAChecklistViewSet(viewsets.ModelViewSet):
    queryset = QAChecklist.objects.all()
    serializer_class = QAChecklistSerializer

class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer

class BugViewSet(viewsets.ModelViewSet):
    queryset = Bug.objects.all()
    serializer_class = BugSerializer

class UATSessionViewSet(viewsets.ModelViewSet):
    queryset = UATSession.objects.all()
    serializer_class = UATSessionSerializer

class WeeklyReportViewSet(viewsets.ModelViewSet):
    queryset = WeeklyReport.objects.all()
    serializer_class = WeeklyReportSerializer

class MonthlyReportViewSet(viewsets.ModelViewSet):
    queryset = MonthlyReport.objects.all()
    serializer_class = MonthlyReportSerializer

class LessonsLearnedViewSet(viewsets.ModelViewSet):
    queryset = LessonsLearned.objects.all()
    serializer_class = LessonsLearnedSerializer

class MeetingMinutesViewSet(viewsets.ModelViewSet):
    queryset = MeetingMinutes.objects.all()
    serializer_class = MeetingMinutesSerializer

class ActionItemViewSet(viewsets.ModelViewSet):
    queryset = ActionItem.objects.all()
    serializer_class = ActionItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'assigned_to']

class DependencyViewSet(viewsets.ModelViewSet):
    queryset = Dependency.objects.all()
    serializer_class = DependencySerializer

class CommunicationPlanViewSet(viewsets.ModelViewSet):
    queryset = CommunicationPlan.objects.all()
    serializer_class = CommunicationPlanSerializer

class DocumentRegisterViewSet(viewsets.ModelViewSet):
    queryset = DocumentRegister.objects.all()
    serializer_class = DocumentRegisterSerializer

class TrainingPlanViewSet(viewsets.ModelViewSet):
    queryset = TrainingPlan.objects.all()
    serializer_class = TrainingPlanSerializer

class GoLiveChecklistViewSet(viewsets.ModelViewSet):
    queryset = GoLiveChecklist.objects.all()
    serializer_class = GoLiveChecklistSerializer

class MaintenancePlanViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePlan.objects.all()
    serializer_class = MaintenancePlanSerializer

class ProjectClosureViewSet(viewsets.ModelViewSet):
    queryset = ProjectClosure.objects.all()
    serializer_class = ProjectClosureSerializer
