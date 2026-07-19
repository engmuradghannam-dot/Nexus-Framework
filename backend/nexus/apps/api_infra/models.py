from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
import uuid


def generate_webhook_secret():
    # A module-level function (not a lambda) so Django's migration writer can
    # serialize this default - lambdas aren't importable/referenceable.
    return uuid.uuid4().hex


class Webhook(models.Model):
    EVENT_CHOICES = [
        ('*', 'All Events'),
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('employee.created', 'Employee Created'),
        ('employee.updated', 'Employee Updated'),
        ('invoice.paid', 'Invoice Paid'),
        ('invoice.overdue', 'Invoice Overdue'),
        ('order.placed', 'Order Placed'),
        ('payment.received', 'Payment Received'),
        ('inventory.low', 'Low Inventory'),
        ('leave.approved', 'Leave Approved'),
        ('task.completed', 'Task Completed'),
    ]

    name = models.CharField(max_length=255)
    url = models.URLField()
    events = models.JSONField(default=list, help_text="List of event names")
    secret = models.CharField(max_length=255, default=generate_webhook_secret)
    is_active = models.BooleanField(default=True)
    retry_count = models.PositiveIntegerField(default=3)
    timeout = models.PositiveIntegerField(default=30)
    headers = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webhooks')
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    success_count = models.PositiveIntegerField(default=0)
    fail_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} -> {self.url}"

class WebhookDelivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    event = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

class FileUpload(models.Model):
    STORAGE_CHOICES = [
        ('local', 'Local Storage'),
        ('s3', 'Amazon S3'),
        ('minio', 'MinIO'),
    ]

    file = models.FileField(upload_to='uploads/%Y/%m/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()
    storage = models.CharField(max_length=20, choices=STORAGE_CHOICES, default='local')
    url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name

class APIRequestLog(models.Model):
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True)
    response_status = models.PositiveIntegerField()
    response_body = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class BatchOperation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]

    OPERATION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    name = models.CharField(max_length=255)
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    model_name = models.CharField(max_length=100)
    total_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    fail_count = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_operations')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
