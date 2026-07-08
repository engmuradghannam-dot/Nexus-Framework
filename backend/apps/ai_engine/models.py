"""AI Engine Module - AI Agents, Feature Control, Deployment Templates, Workflow Library"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Company
User = get_user_model()

class AIAgent(models.Model):
    INDUSTRY = [('Aviation','Aviation'),('Healthcare','Healthcare'),('Manufacturing','Manufacturing'),('Retail','Retail'),('Banking','Banking'),('Energy','Energy'),('Education','Education'),('General','General')]
    STATUS = [('Active','Active'),('Training','Training'),('Inactive','Inactive'),('Error','Error')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ai_agents')
    name = models.CharField(max_length=255)
    agent_type = models.CharField(max_length=50)
    industry = models.CharField(max_length=20, choices=INDUSTRY, default='General')
    description = models.TextField()
    model_endpoint = models.URLField(blank=True)
    model_name = models.CharField(max_length=100, default='gpt-4')
    system_prompt = models.TextField(blank=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.7)
    max_tokens = models.PositiveIntegerField(default=2048)
    status = models.CharField(max_length=20, choices=STATUS, default='Inactive')
    is_enabled = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ['company', 'agent_type']

class AIConversation(models.Model):
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    session_id = models.CharField(max_length=100)
    query = models.TextField()
    response = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    context_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class AIPrediction(models.Model):
    agent = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.CharField(max_length=50)
    target_entity = models.CharField(max_length=255)
    prediction_data = models.JSONField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    recommended_action = models.TextField(blank=True)
    is_actioned = models.BooleanField(default=False)
    actioned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actioned_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']

class FeatureFlag(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='feature_flags')
    feature_name = models.CharField(max_length=100)
    feature_code = models.CharField(max_length=50)
    module = models.CharField(max_length=50)
    is_enabled = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    requires_license = models.BooleanField(default=False)
    license_tier = models.CharField(max_length=50, blank=True)
    config = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ['company', 'feature_code']

class LicensePackage(models.Model):
    TIER = [('Starter','Nexus Starter'),('Business','Nexus Business'),('Industry','Nexus Industry'),('Enterprise','Nexus Enterprise AI')]
    BILLING = [('Monthly','Monthly'),('Annual','Annual'),('Perpetual','Perpetual')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='licenses')
    tier = models.CharField(max_length=20, choices=TIER)
    billing_cycle = models.CharField(max_length=20, choices=BILLING, default='Monthly')
    start_date = models.DateField()
    end_date = models.DateField()
    max_users = models.PositiveIntegerField(default=5)
    max_branches = models.PositiveIntegerField(default=1)
    max_warehouses = models.PositiveIntegerField(default=1)
    modules_enabled = models.JSONField(default=list)
    ai_agents_enabled = models.JSONField(default=list)
    industries_enabled = models.JSONField(default=list)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=20, default='Paid')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.company.name} - {self.tier}"

class DeploymentTemplate(models.Model):
    INDUSTRY = [('Aviation','Aviation'),('Healthcare','Healthcare'),('Hotels','Hotels & Hospitality'),('Manufacturing','Manufacturing'),('Construction','Construction'),('Retail','Retail'),('Banking','Banking'),('Government','Government'),('Energy','Energy'),('Education','Education'),('General','General ERP')]
    SIZE = [('Small','Small'),('Medium','Medium'),('Large','Large'),('Enterprise','Enterprise')]
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=20, choices=INDUSTRY)
    country = models.CharField(max_length=100)
    company_size = models.CharField(max_length=20, choices=SIZE)
    description = models.TextField(blank=True)
    modules_to_install = models.JSONField(default=list)
    ai_agents_to_enable = models.JSONField(default=list)
    regulatory_requirements = models.JSONField(default=list)
    default_settings = models.JSONField(default=dict)
    recommended_license = models.CharField(max_length=20, default='Starter')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['industry', 'country', 'company_size']

class WorkflowTemplate(models.Model):
    CATEGORY = [('Purchase','Purchase'),('Sales','Sales'),('HR','HR'),('Finance','Finance'),('Inventory','Inventory'),('Project','Project'),('Approval','Approval'),('Custom','Custom')]
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY)
    description = models.TextField(blank=True)
    steps = models.JSONField(default=list)
    transitions = models.JSONField(default=list)
    conditions = models.JSONField(default=dict, blank=True)
    notifications = models.JSONField(default=list, blank=True)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class APIIntegration(models.Model):
    TYPE = [('Banking','Banking'),('Government','Government'),('AI','AI Model'),('Payment','Payment Gateway'),('SMS','SMS'),('Email','Email'),('Other','Other')]
    AUTH = [('API Key','API Key'),('OAuth2','OAuth2'),('Basic','Basic Auth'),('Bearer','Bearer Token'),('Certificate','Client Certificate')]
    STATUS = [('Active','Active'),('Inactive','Inactive'),('Error','Error'),('Testing','Testing')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='api_integrations')
    name = models.CharField(max_length=255)
    integration_type = models.CharField(max_length=20, choices=TYPE)
    provider = models.CharField(max_length=255)
    base_url = models.URLField()
    auth_type = models.CharField(max_length=20, choices=AUTH)
    credentials = models.JSONField(default=dict, blank=True)
    endpoints = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Inactive')
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.CharField(max_length=50, default='Manual')
    error_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['company', 'name']

class DataDictionary(models.Model):
    entity_name = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    related_entity = models.CharField(max_length=100, blank=True)
    validation_rules = models.JSONField(default=dict, blank=True)
    module = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ['entity_name', 'field_name']
        ordering = ['module', 'entity_name', 'field_name']
