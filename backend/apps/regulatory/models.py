"""Regulatory & Compliance Module - ZATCA, GDPR, GAAP, HIPAA"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Company
User = get_user_model()

class TaxConfiguration(models.Model):
    TAX_TYPE = [('VAT','VAT'),('GST','GST'),('Corporate','Corporate Tax'),('Income','Income Tax'),('Withholding','Withholding Tax'),('Zakat','Zakat')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tax_configs')
    country = models.CharField(max_length=100)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE)
    tax_name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_compound = models.BooleanField(default=False)
    is_inclusive = models.BooleanField(default=False)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    zatca_enabled = models.BooleanField(default=False)
    zatca_api_key = models.CharField(max_length=255, blank=True)
    zatca_environment = models.CharField(max_length=20, default='Sandbox', blank=True)
    zatca_compliance_checks = models.JSONField(default=list, blank=True)
    class Meta:
        unique_together = ['company', 'country', 'tax_type']

class ZATCAInvoice(models.Model):
    STATUS = [('Draft','Draft'),('Submitted','Submitted'),('Clearance','Clearance Pending'),('Cleared','Cleared'),('Rejected','Rejected'),('Reported','Reported')]
    INVOICE_TYPE = [('Standard','Standard'),('Simplified','Simplified'),('Credit','Credit Note'),('Debit','Debit Note')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='zatca_invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE, default='Standard')
    issue_date = models.DateTimeField()
    supplier_name = models.CharField(max_length=255)
    supplier_vat = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=255, blank=True)
    customer_vat = models.CharField(max_length=50, blank=True)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_with_vat = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    xml_content = models.TextField(blank=True)
    qr_code = models.TextField(blank=True)
    uuid = models.CharField(max_length=100, unique=True)
    previous_invoice_hash = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Draft')
    zatca_response = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class GDPRConsent(models.Model):
    CONSENT_TYPE = [('Marketing','Marketing'),('Analytics','Analytics'),('Necessary','Necessary'),('Preferences','Preferences'),('ThirdParty','Third Party')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gdpr_consents')
    user_email = models.EmailField()
    consent_type = models.CharField(max_length=20, choices=CONSENT_TYPE)
    is_granted = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    consent_version = models.CharField(max_length=20, default='1.0')
    document_url = models.URLField(blank=True)
    class Meta:
        unique_together = ['company', 'user_email', 'consent_type']

class DataSubjectRequest(models.Model):
    REQUEST_TYPE = [('Access','Access'),('Rectification','Rectification'),('Erasure','Erasure'),('Restriction','Restriction'),('Portability','Portability'),('Objection','Objection')]
    STATUS = [('Received','Received'),('In Review','In Review'),('Processing','Processing'),('Completed','Completed'),('Rejected','Rejected')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='dsar_requests')
    request_id = models.CharField(max_length=50, unique=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE)
    requester_email = models.EmailField()
    requester_name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='Received')
    received_date = models.DateTimeField(auto_now_add=True)
    deadline_date = models.DateField()
    completed_date = models.DateTimeField(null=True, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

class ComplianceAudit(models.Model):
    FRAMEWORK = [('GDPR','GDPR'),('HIPAA','HIPAA'),('SOC2','SOC2'),('ISO27001','ISO 27001'),('ZATCA','ZATCA'),('GAAP','GAAP'),('IFRS','IFRS')]
    STATUS = [('Planned','Planned'),('In Progress','In Progress'),('Completed','Completed'),('Failed','Failed')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='compliance_audits')
    audit_id = models.CharField(max_length=50, unique=True)
    framework = models.CharField(max_length=20, choices=FRAMEWORK)
    audit_date = models.DateField()
    auditor = models.CharField(max_length=255)
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Planned')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    next_audit_date = models.DateField(null=True, blank=True)
    documents = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class HIPAAAuditLog(models.Model):
    ACTION = [('View','View'),('Create','Create'),('Update','Update'),('Delete','Delete'),('Export','Export'),('Print','Print')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='hipaa_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=50)
    patient_id = models.CharField(max_length=50, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_phi = models.BooleanField(default=False)
    class Meta:
        ordering = ['-timestamp']
