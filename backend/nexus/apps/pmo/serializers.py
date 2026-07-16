from rest_framework import serializers
from .models import Project, Task, Milestone

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    task_count = serializers.IntegerField(source='tasks.count', read_only=True)
    completed_tasks = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(completed=True).count()
