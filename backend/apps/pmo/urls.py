"""PMO URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectCharterViewSet, BusinessCaseViewSet, StakeholderViewSet,
    RequirementViewSet, WBSViewSet, DeliverableViewSet,
    MilestoneViewSet, SprintViewSet, KanbanBoardViewSet,
    KanbanCardViewSet, ResourceViewSet, RACIViewSet,
    RiskViewSet, IssueViewSet, ChangeRequestViewSet,
    DecisionLogViewSet, QualityPlanViewSet, QAChecklistViewSet,
    TestCaseViewSet, BugViewSet, UATSessionViewSet,
    WeeklyReportViewSet, MonthlyReportViewSet, LessonsLearnedViewSet,
    MeetingMinutesViewSet, ActionItemViewSet, DependencyViewSet,
    CommunicationPlanViewSet, DocumentRegisterViewSet,
    TrainingPlanViewSet, GoLiveChecklistViewSet,
    MaintenancePlanViewSet, ProjectClosureViewSet
)

router = DefaultRouter()
router.register(r'project-charters', ProjectCharterViewSet)
router.register(r'business-cases', BusinessCaseViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'requirements', RequirementViewSet)
router.register(r'wbs', WBSViewSet)
router.register(r'deliverables', DeliverableViewSet)
router.register(r'milestones', MilestoneViewSet)
router.register(r'sprints', SprintViewSet)
router.register(r'kanban-boards', KanbanBoardViewSet)
router.register(r'kanban-cards', KanbanCardViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'raci', RACIViewSet)
router.register(r'risks', RiskViewSet)
router.register(r'issues', IssueViewSet)
router.register(r'change-requests', ChangeRequestViewSet)
router.register(r'decisions', DecisionLogViewSet)
router.register(r'quality-plans', QualityPlanViewSet)
router.register(r'qa-checklists', QAChecklistViewSet)
router.register(r'test-cases', TestCaseViewSet)
router.register(r'bugs', BugViewSet)
router.register(r'uat-sessions', UATSessionViewSet)
router.register(r'weekly-reports', WeeklyReportViewSet)
router.register(r'monthly-reports', MonthlyReportViewSet)
router.register(r'lessons-learned', LessonsLearnedViewSet)
router.register(r'meeting-minutes', MeetingMinutesViewSet)
router.register(r'action-items', ActionItemViewSet)
router.register(r'dependencies', DependencyViewSet)
router.register(r'communication-plans', CommunicationPlanViewSet)
router.register(r'documents', DocumentRegisterViewSet)
router.register(r'training-plans', TrainingPlanViewSet)
router.register(r'go-live-checklist', GoLiveChecklistViewSet)
router.register(r'maintenance-plans', MaintenancePlanViewSet)
router.register(r'project-closures', ProjectClosureViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
