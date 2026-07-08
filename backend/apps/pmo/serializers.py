"""PMO Serializers"""
from rest_framework import serializers
from .models import (
    ProjectCharter, BusinessCase, Stakeholder, Requirement, WBS,
    Deliverable, Milestone, Sprint, KanbanBoard, KanbanCard,
    Resource, RACI, Risk, Issue, ChangeRequest, DecisionLog,
    QualityPlan, QAChecklist, TestCase, Bug, UATSession,
    WeeklyReport, MonthlyReport, LessonsLearned, MeetingMinutes,
    ActionItem, Dependency, CommunicationPlan, DocumentRegister,
    TrainingPlan, GoLiveChecklist, MaintenancePlan, ProjectClosure
)

class ProjectCharterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCharter
        fields = '__all__'

class BusinessCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCase
        fields = '__all__'

class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = '__all__'

class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = '__all__'

class WBSSerializer(serializers.ModelSerializer):
    class Meta:
        model = WBS
        fields = '__all__'

class DeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliverable
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = '__all__'

class KanbanBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanBoard
        fields = '__all__'

class KanbanCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanCard
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'

class RACISerializer(serializers.ModelSerializer):
    class Meta:
        model = RACI
        fields = '__all__'

class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = '__all__'

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'

class ChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeRequest
        fields = '__all__'

class DecisionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionLog
        fields = '__all__'

class QualityPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityPlan
        fields = '__all__'

class QAChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = QAChecklist
        fields = '__all__'

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = '__all__'

class BugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bug
        fields = '__all__'

class UATSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UATSession
        fields = '__all__'

class WeeklyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyReport
        fields = '__all__'

class MonthlyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReport
        fields = '__all__'

class LessonsLearnedSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonsLearned
        fields = '__all__'

class MeetingMinutesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingMinutes
        fields = '__all__'

class ActionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionItem
        fields = '__all__'

class DependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependency
        fields = '__all__'

class CommunicationPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationPlan
        fields = '__all__'

class DocumentRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentRegister
        fields = '__all__'

class TrainingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPlan
        fields = '__all__'

class GoLiveChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoLiveChecklist
        fields = '__all__'

class MaintenancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenancePlan
        fields = '__all__'

class ProjectClosureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectClosure
        fields = '__all__'
