from rest_framework import serializers
from apps.core.workflow import validate_transition
from .models import Project, Task, Milestone, Stakeholder, RiskRegister, IssueLog, ChangeRequest, TimeEntry, TaskComment

CR_TRANSITIONS = {
    'Pending': {'Approved', 'Rejected'},
    'Approved': {'Implemented'},
    'Rejected': set(),
    'Implemented': set(),
}


class ProjectSerializer(serializers.ModelSerializer):
    progress_percent = serializers.ReadOnlyField()
    budget_variance = serializers.ReadOnlyField()
    total_hours_logged = serializers.SerializerMethodField()
    total_cost_logged = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_total_hours_logged(self, obj):
        return sum((te.duration_hours for te in obj.time_entries.all()), 0)

    def get_total_cost_logged(self, obj):
        return sum((te.cost for te in obj.time_entries.all()), 0)


class TaskSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()
    assignee_name = serializers.CharField(source='assigned_to.first_name', read_only=True, default=None)
    team_name = serializers.CharField(source='team.name', read_only=True, default=None)

    class Meta:
        model = Task
        fields = '__all__'

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_total_hours(self, obj):
        return sum((te.duration_hours for te in obj.time_entries.all()), 0)


class MilestoneSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    tasks_count = serializers.SerializerMethodField()
    completed_tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Milestone
        fields = '__all__'

    def get_tasks_count(self, obj):
        return obj.project.tasks.filter(expected_end__lte=obj.due_date).count()

    def get_completed_tasks_count(self, obj):
        return obj.project.tasks.filter(
            expected_end__lte=obj.due_date,
            status='Completed'
        ).count()


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = '__all__'


class RiskRegisterSerializer(serializers.ModelSerializer):
    risk_score = serializers.ReadOnlyField()
    risk_level = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.first_name', read_only=True, default=None)

    class Meta:
        model = RiskRegister
        fields = '__all__'


class IssueLogSerializer(serializers.ModelSerializer):
    raised_by_name = serializers.CharField(source='raised_by.first_name', read_only=True, default=None)
    assigned_to_name = serializers.CharField(source='assigned_to.first_name', read_only=True, default=None)

    class Meta:
        model = IssueLog
        fields = '__all__'


class ChangeRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.first_name', read_only=True, default=None)
    approved_by_name = serializers.CharField(source='approved_by.first_name', read_only=True, default=None)

    class Meta:
        model = ChangeRequest
        fields = '__all__'

    def validate(self, data):
        new_status = data.get('status')
        if self.instance and new_status and new_status != self.instance.status:
            validate_transition(CR_TRANSITIONS, self.instance.status, new_status)
        return data


class TimeEntrySerializer(serializers.ModelSerializer):
    duration_hours = serializers.ReadOnlyField()
    cost = serializers.ReadOnlyField()
    employee_name = serializers.CharField(source='employee.first_name', read_only=True, default=None)
    task_subject = serializers.CharField(source='task.subject', read_only=True, default=None)
    project_name = serializers.CharField(source='project.project_name', read_only=True, default=None)

    class Meta:
        model = TimeEntry
        fields = '__all__'

    def validate(self, data):
        start = data.get('start_time', getattr(self.instance, 'start_time', None))
        end = data.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and end < start:
            raise serializers.ValidationError("End time cannot be before start time.")
        return data


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.email', read_only=True)
    author_initials = serializers.SerializerMethodField()
    reply_count = serializers.ReadOnlyField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = '__all__'

    def get_author_initials(self, obj):
        name = obj.author.email or 'User'
        parts = name.split('@')[0].split('.')
        return ''.join([p[0].upper() for p in parts if p])[:2]

    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.author == request.user
        return False
