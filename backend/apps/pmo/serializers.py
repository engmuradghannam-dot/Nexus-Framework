from rest_framework import serializers

from django.core.exceptions import ValidationError as DjangoValidationError

from .models import check_resource_allocation  # noqa: F401
from .models import Milestone, Portfolio, Project, Task


class PortfolioSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source="manager.get_full_name", read_only=True)
    project_count = serializers.IntegerField(source="projects.count", read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "description",
            "manager",
            "manager_name",
            "status",
            "start_date",
            "end_date",
            "budget",
            "project_count",
            "created_at",
            "updated_at",
        ]


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(
        source="assignee.get_full_name", read_only=True
    )
    project_name = serializers.CharField(source="project.name", read_only=True)
    subtask_count = serializers.IntegerField(source="subtasks.count", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "assignee",
            "assignee_name",
            "status",
            "priority",
            "parent_task",
            "subtask_count",
            "milestone",
            "start_date",
            "due_date",
            "estimated_hours",
            "actual_hours",
            "duration_days",
            "predecessors",
            "early_start",
            "early_finish",
            "late_start",
            "late_finish",
            "slack",
            "is_critical",
            "created_at",
        ]
        read_only_fields = [
            "early_start", "early_finish", "late_start", "late_finish",
            "slack", "is_critical",
        ]

    def validate(self, data):
        """PRJ-CTRL-002 (milestone gate) and PRJ-CTRL-003 (resource capacity)
        are preventive: they must block the save, not report afterwards."""
        probe = self.instance or Task(**{
            k: v for k, v in data.items() if k != "predecessors"
        })
        for k, v in data.items():
            if k != "predecessors":
                setattr(probe, k, v)

        new_status = data.get("status", getattr(self.instance, "status", None))
        old_status = getattr(self.instance, "status", None)
        if new_status == "In Progress" and old_status != "In Progress" and probe.project_id:
            try:
                probe.project.check_milestone_gate(probe)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages[0])

        try:
            check_resource_allocation(probe.assignee, probe)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0])
        return data


class MilestoneSerializer(serializers.ModelSerializer):
    is_achieved = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Milestone
        fields = [
            "id",
            "project",
            "name",
            "target_date",
            "achieved_date",
            "description",
            "is_achieved",
            "is_overdue",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    budget_utilization = serializers.FloatField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    task_count = serializers.IntegerField(source="tasks.count", read_only=True)
    completed_tasks = serializers.SerializerMethodField()
    milestone_count = serializers.IntegerField(
        source="milestones.count", read_only=True
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "code",
            "description",
            "status",
            "priority",
            "owner",
            "owner_name",
            "start_date",
            "end_date",
            "actual_start_date",
            "actual_end_date",
            "budget",
            "spent",
            "budget_utilization",
            "progress",
            "is_overdue",
            "branch",
            "branch_name",
            "task_count",
            "completed_tasks",
            "milestone_count",
            "created_at",
            "updated_at",
        ]

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(status="done").count()
