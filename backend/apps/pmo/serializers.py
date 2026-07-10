from rest_framework import serializers

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
            "due_date",
            "estimated_hours",
            "actual_hours",
            "created_at",
        ]


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
