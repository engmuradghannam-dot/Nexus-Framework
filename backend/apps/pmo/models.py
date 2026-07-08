"""PMO Module - 33 Models"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Company
User = get_user_model()

class ProjectCharter(models.Model):
    STATUS = [('Draft','Draft'),('Approved','Approved'),('Rejected','Rejected'),('On Hold','On Hold')]
    PRIORITY = [('P1','Critical'),('P2','High'),('P3','Medium'),('P4','Low')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='charters')
    project_code = models.CharField(max_length=50, unique=True)
    project_name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_charters')
    sponsor = models.CharField(max_length=255, blank=True)
    business_case = models.TextField(blank=True)
    objectives = models.JSONField(default=list)
    scope_in = models.TextField(blank=True)
    scope_out = models.TextField(blank=True)
    budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    actual_spend = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50, choices=STATUS, default='Draft')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='P3')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-priority', '-created_at']

class BusinessCase(models.Model):
    charter = models.OneToOneField(ProjectCharter, on_delete=models.CASCADE, related_name='business_case')
    problem_statement = models.TextField()
    proposed_solution = models.TextField()
    benefits = models.JSONField(default=list)
    costs = models.JSONField(default=list)
    roi_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    payback_period_months = models.PositiveIntegerField(default=0)
    npv = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    irr = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_assessment = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Stakeholder(models.Model):
    INFLUENCE = [('High','High'),('Medium','Medium'),('Low','Low')]
    INTEREST = [('High','High'),('Medium','Medium'),('Low','Low')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='stakeholders')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    influence = models.CharField(max_length=10, choices=INFLUENCE, default='Medium')
    interest = models.CharField(max_length=10, choices=INTEREST, default='Medium')
    engagement_strategy = models.TextField(blank=True)
    expectations = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ['charter', 'email']

class Requirement(models.Model):
    TYPE = [('Functional','Functional'),('Non-Functional','Non-Functional'),('Technical','Technical'),('Business','Business')]
    PRIORITY = [('Must','Must'),('Should','Should'),('Could','Could'),('Wont','Wont')]
    STATUS = [('Draft','Draft'),('Reviewed','Reviewed'),('Approved','Approved'),('Implemented','Implemented'),('Tested','Tested'),('Rejected','Rejected')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='requirements')
    req_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    req_type = models.CharField(max_length=20, choices=TYPE, default='Functional')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='Must')
    status = models.CharField(max_length=20, choices=STATUS, default='Draft')
    acceptance_criteria = models.TextField(blank=True)
    source = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['charter', 'req_id']

class WBS(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='wbs_items')
    wbs_code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.PositiveIntegerField(default=1)
    is_work_package = models.BooleanField(default=False)
    estimated_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['wbs_code']
        unique_together = ['charter', 'wbs_code']

class Deliverable(models.Model):
    STATUS = [('Planned','Planned'),('In Progress','In Progress'),('Review','Under Review'),('Approved','Approved'),('Rejected','Rejected')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='deliverables')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    wbs = models.ForeignKey(WBS, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Planned')
    acceptance_criteria = models.TextField(blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_deliverables')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_deliverables')
    document_url = models.URLField(blank=True)

class Milestone(models.Model):
    STATUS = [('Planned','Planned'),('At Risk','At Risk'),('Achieved','Achieved'),('Missed','Missed'),('Deferred','Deferred')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Planned')
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False)
    is_critical = models.BooleanField(default=False)
    gate_criteria = models.TextField(blank=True)

class Sprint(models.Model):
    STATUS = [('Planning','Planning'),('Active','Active'),('Review','Review'),('Retrospective','Retrospective'),('Closed','Closed')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='sprints')
    sprint_number = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='Planning')
    total_story_points = models.PositiveIntegerField(default=0)
    completed_story_points = models.PositiveIntegerField(default=0)
    velocity = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    retrospective_notes = models.TextField(blank=True)
    class Meta:
        ordering = ['-sprint_number']
        unique_together = ['charter', 'sprint_number']

class KanbanBoard(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='kanban_boards')
    name = models.CharField(max_length=255)
    columns = models.JSONField(default=list)
    wip_limits = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class KanbanCard(models.Model):
    PRIORITY = [('Low','Low'),('Medium','Medium'),('High','High'),('Critical','Critical')]
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    column = models.CharField(max_length=50, default='Backlog')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='Medium')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    story_points = models.PositiveIntegerField(default=0)
    tags = models.JSONField(default=list)
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['column', 'order']

class Resource(models.Model):
    TYPE = [('Human','Human'),('Material','Material'),('Equipment','Equipment'),('Budget','Budget')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='resources')
    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=TYPE, default='Human')
    skill_set = models.JSONField(default=list, blank=True)
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    availability_start = models.DateField()
    availability_end = models.DateField()
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class RACI(models.Model):
    ROLE = [('R','Responsible'),('A','Accountable'),('C','Consulted'),('I','Informed')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='raci_matrix')
    task = models.CharField(max_length=255)
    wbs = models.ForeignKey(WBS, on_delete=models.SET_NULL, null=True, blank=True)
    person = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=1, choices=ROLE, default='R')
    class Meta:
        unique_together = ['charter', 'task', 'person']

class Risk(models.Model):
    CATEGORY = [('Technical','Technical'),('Schedule','Schedule'),('Cost','Cost'),('Resource','Resource'),('External','External'),('Organizational','Organizational')]
    STATUS = [('Open','Open'),('Mitigated','Mitigated'),('Closed','Closed'),('Accepted','Accepted')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='risks')
    risk_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY, default='Technical')
    probability = models.PositiveIntegerField(choices=[(1,'Very Low'),(2,'Low'),(3,'Medium'),(4,'High'),(5,'Very High')], default=3)
    impact = models.PositiveIntegerField(choices=[(1,'Negligible'),(2,'Minor'),(3,'Moderate'),(4,'Major'),(5,'Catastrophic')], default=3)
    risk_score = models.PositiveIntegerField(default=9)
    mitigation_strategy = models.TextField(blank=True)
    contingency_plan = models.TextField(blank=True)
    risk_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Open')
    trigger_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ['charter', 'risk_id']
        ordering = ['-risk_score', '-created_at']
    def save(self, *args, **kwargs):
        self.risk_score = self.probability * self.impact
        super().save(*args, **kwargs)

class Issue(models.Model):
    SEVERITY = [('Critical','Critical'),('Major','Major'),('Minor','Minor'),('Cosmetic','Cosmetic')]
    STATUS = [('Open','Open'),('In Progress','In Progress'),('Resolved','Resolved'),('Closed','Closed'),('Reopened','Reopened')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='issues')
    issue_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY, default='Minor')
    status = models.CharField(max_length=20, choices=STATUS, default='Open')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_issues')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_issues')
    reported_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True)
    related_risk = models.ForeignKey(Risk, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        unique_together = ['charter', 'issue_id']

class ChangeRequest(models.Model):
    TYPE = [('Scope','Scope'),('Schedule','Schedule'),('Cost','Cost'),('Quality','Quality')]
    STATUS = [('Submitted','Submitted'),('Under Review','Under Review'),('Approved','Approved'),('Rejected','Rejected'),('Implemented','Implemented')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='change_requests')
    cr_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    change_type = models.CharField(max_length=20, choices=TYPE, default='Scope')
    justification = models.TextField()
    impact_analysis = models.TextField(blank=True)
    cost_impact = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    schedule_impact_days = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='Submitted')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_changes')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_changes')
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = ['charter', 'cr_id']

class DecisionLog(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='decisions')
    decision_id = models.CharField(max_length=50)
    decision = models.TextField()
    context = models.TextField(blank=True)
    alternatives_considered = models.TextField(blank=True)
    decision_maker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    impact = models.TextField(blank=True)
    class Meta:
        unique_together = ['charter', 'decision_id']

class QualityPlan(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='quality_plans')
    standard = models.CharField(max_length=255, blank=True)
    quality_objectives = models.JSONField(default=list)
    metrics = models.JSONField(default=list)
    review_frequency = models.CharField(max_length=50, default='Monthly')
    audit_schedule = models.JSONField(default=list)

class QAChecklist(models.Model):
    STATUS = [('Pending','Pending'),('Pass','Pass'),('Fail','Fail'),('N/A','N/A')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='qa_checklists')
    category = models.CharField(max_length=255)
    item = models.TextField()
    criteria = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='Pending')
    checked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    checked_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

class TestCase(models.Model):
    TYPE = [('Unit','Unit'),('Integration','Integration'),('System','System'),('UAT','UAT'),('Regression','Regression')]
    STATUS = [('Draft','Draft'),('Ready','Ready'),('Executed','Executed'),('Passed','Passed'),('Failed','Failed'),('Blocked','Blocked')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='test_cases')
    tc_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    test_type = models.CharField(max_length=20, choices=TYPE, default='Unit')
    preconditions = models.TextField(blank=True)
    steps = models.JSONField(default=list)
    expected_result = models.TextField()
    actual_result = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Draft')
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    executed_date = models.DateTimeField(null=True, blank=True)
    related_requirement = models.ForeignKey(Requirement, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        unique_together = ['charter', 'tc_id']

class Bug(models.Model):
    SEVERITY = [('Critical','Critical'),('Major','Major'),('Minor','Minor'),('Trivial','Trivial')]
    STATUS = [('New','New'),('Confirmed','Confirmed'),('In Progress','In Progress'),('Fixed','Fixed'),('Verified','Verified'),('Closed','Closed'),('Reopened','Reopened')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='bugs')
    bug_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY, default='Minor')
    status = models.CharField(max_length=20, choices=STATUS, default='New')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_bugs')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bugs')
    reported_date = models.DateTimeField(auto_now_add=True)
    fixed_date = models.DateTimeField(null=True, blank=True)
    fix_version = models.CharField(max_length=50, blank=True)
    related_test_case = models.ForeignKey(TestCase, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        unique_together = ['charter', 'bug_id']

class UATSession(models.Model):
    STATUS = [('Planned','Planned'),('In Progress','In Progress'),('Completed','Completed'),('Failed','Failed')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='uat_sessions')
    name = models.CharField(max_length=255)
    test_scenarios = models.JSONField(default=list)
    testers = models.ManyToManyField(User, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='Planned')
    sign_off_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sign_off_date = models.DateField(null=True, blank=True)
    feedback = models.TextField(blank=True)

class WeeklyReport(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='weekly_reports')
    week_ending = models.DateField()
    accomplishments = models.JSONField(default=list)
    upcoming_tasks = models.JSONField(default=list)
    issues_blockers = models.JSONField(default=list)
    budget_status = models.TextField(blank=True)
    schedule_status = models.TextField(blank=True)
    risks_summary = models.TextField(blank=True)
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['charter', 'week_ending']

class MonthlyReport(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='monthly_reports')
    month = models.DateField()
    executive_summary = models.TextField()
    kpi_metrics = models.JSONField(default=dict)
    budget_variance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    schedule_variance_days = models.IntegerField(default=0)
    milestone_status = models.JSONField(default=list)
    risk_summary = models.TextField(blank=True)
    resource_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_monthly')
    class Meta:
        unique_together = ['charter', 'month']

class LessonsLearned(models.Model):
    CATEGORY = [('Technical','Technical'),('Process','Process'),('Communication','Communication'),('Management','Management')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='lessons_learned')
    category = models.CharField(max_length=20, choices=CATEGORY, default='Technical')
    what_happened = models.TextField()
    why_it_happened = models.TextField()
    what_we_learned = models.TextField()
    recommendations = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateField(auto_now_add=True)
    is_actionable = models.BooleanField(default=True)

class MeetingMinutes(models.Model):
    TYPE = [('Standup','Standup'),('Review','Review'),('Retrospective','Retrospective'),('Stakeholder','Stakeholder'),('Other','Other')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='meeting_minutes')
    meeting_type = models.CharField(max_length=20, choices=TYPE, default='Other')
    date = models.DateTimeField()
    attendees = models.ManyToManyField(User, blank=True)
    agenda = models.JSONField(default=list)
    discussion_points = models.JSONField(default=list)
    decisions = models.JSONField(default=list)
    action_items = models.JSONField(default=list)
    next_meeting_date = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class ActionItem(models.Model):
    STATUS = [('Open','Open'),('In Progress','In Progress'),('Completed','Completed'),('Overdue','Overdue'),('Cancelled','Cancelled')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='action_items')
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_actions')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='Open')
    priority = models.CharField(max_length=10, choices=ProjectCharter.PRIORITY, default='P3')
    source = models.CharField(max_length=255, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ['due_date', '-priority']

class Dependency(models.Model):
    TYPE = [('Internal','Internal'),('External','External')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='dependencies')
    dependency = models.CharField(max_length=255)
    dependency_type = models.CharField(max_length=10, choices=TYPE, default='Internal')
    dependent_task = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    expected_date = models.DateField()
    status = models.CharField(max_length=20, default='Open')
    impact_if_delayed = models.TextField(blank=True)

class CommunicationPlan(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='communication_plans')
    stakeholder_group = models.CharField(max_length=255)
    information_needed = models.TextField()
    frequency = models.CharField(max_length=50)
    method = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    distribution_list = models.JSONField(default=list)

class DocumentRegister(models.Model):
    TYPE = [('Plan','Plan'),('Report','Report'),('Specification','Specification'),('Drawing','Drawing'),('Other','Other')]
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='documents')
    doc_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=TYPE, default='Other')
    version = models.CharField(max_length=20, default='1.0')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_date = models.DateField(auto_now_add=True)
    review_date = models.DateField(null=True, blank=True)
    approval_status = models.CharField(max_length=20, default='Draft')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_docs')
    file_url = models.URLField(blank=True)
    is_current = models.BooleanField(default=True)
    class Meta:
        unique_together = ['charter', 'doc_id']

class TrainingPlan(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='training_plans')
    topic = models.CharField(max_length=255)
    audience = models.CharField(max_length=255)
    delivery_method = models.CharField(max_length=50)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    scheduled_date = models.DateField()
    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    completion_status = models.CharField(max_length=20, default='Planned')
    attendees = models.ManyToManyField(User, blank=True, related_name='trainings_attended')

class GoLiveChecklist(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='go_live_checklist')
    item = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    is_completed = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

class MaintenancePlan(models.Model):
    charter = models.ForeignKey(ProjectCharter, on_delete=models.CASCADE, related_name='maintenance_plans')
    activity = models.CharField(max_length=255)
    frequency = models.CharField(max_length=50)
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='Planned')

class ProjectClosure(models.Model):
    charter = models.OneToOneField(ProjectCharter, on_delete=models.CASCADE, related_name='closure')
    closure_date = models.DateField()
    final_budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    final_spend = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    budget_variance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    schedule_variance_days = models.IntegerField(default=0)
    deliverables_status = models.JSONField(default=list)
    handover_complete = models.BooleanField(default=False)
    documentation_complete = models.BooleanField(default=False)
    lessons_documented = models.BooleanField(default=False)
    team_released = models.BooleanField(default=False)
    signed_off_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    closure_notes = models.TextField(blank=True)
