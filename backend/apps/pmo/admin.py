"""PMO Admin"""
from django.contrib import admin
from .models import (
    ProjectCharter, BusinessCase, Stakeholder, Requirement, WBS,
    Deliverable, Milestone, Sprint, KanbanBoard, KanbanCard,
    Resource, RACI, Risk, Issue, ChangeRequest, DecisionLog,
    QualityPlan, QAChecklist, TestCase, Bug, UATSession,
    WeeklyReport, MonthlyReport, LessonsLearned, MeetingMinutes,
    ActionItem, Dependency, CommunicationPlan, DocumentRegister,
    TrainingPlan, GoLiveChecklist, MaintenancePlan, ProjectClosure
)

@admin.register(ProjectCharter)
class ProjectCharterAdmin(admin.ModelAdmin):
    list_display = ['project_code', 'project_name', 'status', 'priority', 'progress', 'owner']
    list_filter = ['status', 'priority', 'company']
    search_fields = ['project_name', 'project_code']

@admin.register(BusinessCase)
class BusinessCaseAdmin(admin.ModelAdmin):
    list_display = ['charter', 'roi_percentage', 'npv', 'approval_date']

@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'influence', 'interest', 'is_active']
    list_filter = ['influence', 'interest']

@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['req_id', 'title', 'req_type', 'priority', 'status']
    list_filter = ['req_type', 'priority', 'status']

@admin.register(WBS)
class WBSAdmin(admin.ModelAdmin):
    list_display = ['wbs_code', 'name', 'level', 'is_work_package', 'progress']
    list_filter = ['level', 'is_work_package']

@admin.register(Deliverable)
class DeliverableAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'due_date', 'completed_date']
    list_filter = ['status']

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_date', 'status', 'is_critical']
    list_filter = ['status', 'is_critical']

@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['sprint_number', 'name', 'status', 'velocity']
    list_filter = ['status']

@admin.register(KanbanBoard)
class KanbanBoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'charter']

@admin.register(KanbanCard)
class KanbanCardAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'priority', 'assignee']
    list_filter = ['column', 'priority']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource_type', 'allocation_percentage', 'is_active']
    list_filter = ['resource_type', 'is_active']

@admin.register(RACI)
class RACIAdmin(admin.ModelAdmin):
    list_display = ['task', 'person', 'role']
    list_filter = ['role']

@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ['risk_id', 'title', 'risk_score', 'status', 'category']
    list_filter = ['status', 'category', 'probability', 'impact']
    search_fields = ['title', 'description']

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['issue_id', 'title', 'severity', 'status']
    list_filter = ['severity', 'status']

@admin.register(ChangeRequest)
class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['cr_id', 'title', 'change_type', 'status', 'cost_impact']
    list_filter = ['change_type', 'status']

@admin.register(DecisionLog)
class DecisionLogAdmin(admin.ModelAdmin):
    list_display = ['decision_id', 'decision_maker', 'date']

@admin.register(QualityPlan)
class QualityPlanAdmin(admin.ModelAdmin):
    list_display = ['charter', 'standard', 'review_frequency']

@admin.register(QAChecklist)
class QAChecklistAdmin(admin.ModelAdmin):
    list_display = ['category', 'item', 'status']
    list_filter = ['status']

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['tc_id', 'title', 'test_type', 'status']
    list_filter = ['test_type', 'status']

@admin.register(Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = ['bug_id', 'title', 'severity', 'status']
    list_filter = ['severity', 'status']

@admin.register(UATSession)
class UATSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'start_date', 'end_date']
    list_filter = ['status']

@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = ['charter', 'week_ending', 'prepared_by']

@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ['charter', 'month', 'budget_variance', 'schedule_variance_days']

@admin.register(LessonsLearned)
class LessonsLearnedAdmin(admin.ModelAdmin):
    list_display = ['category', 'what_happened', 'date']
    list_filter = ['category']

@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(admin.ModelAdmin):
    list_display = ['meeting_type', 'date', 'recorded_by']
    list_filter = ['meeting_type']

@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ['description', 'assigned_to', 'due_date', 'status', 'priority']
    list_filter = ['status', 'priority']

@admin.register(Dependency)
class DependencyAdmin(admin.ModelAdmin):
    list_display = ['dependency', 'dependency_type', 'expected_date', 'status']
    list_filter = ['dependency_type', 'status']

@admin.register(CommunicationPlan)
class CommunicationPlanAdmin(admin.ModelAdmin):
    list_display = ['stakeholder_group', 'frequency', 'method']

@admin.register(DocumentRegister)
class DocumentRegisterAdmin(admin.ModelAdmin):
    list_display = ['doc_id', 'title', 'doc_type', 'version', 'is_current']
    list_filter = ['doc_type', 'is_current']

@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ['topic', 'audience', 'scheduled_date', 'completion_status']

@admin.register(GoLiveChecklist)
class GoLiveChecklistAdmin(admin.ModelAdmin):
    list_display = ['item', 'category', 'is_completed']
    list_filter = ['is_completed']

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ['activity', 'frequency', 'status']
    list_filter = ['status']

@admin.register(ProjectClosure)
class ProjectClosureAdmin(admin.ModelAdmin):
    list_display = ['charter', 'closure_date', 'handover_complete', 'documentation_complete']
