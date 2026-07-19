from django.db import models
from django.contrib.auth.models import User, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    django_permissions = models.ManyToManyField(DjangoPermission, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nexus_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='user_roles')
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'role', 'branch']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class FieldPermission(models.Model):
    ACCESS_CHOICES = [
        ('hidden', 'Hidden'),
        ('read_only', 'Read Only'),
        ('read_write', 'Read & Write'),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='field_permissions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='read_write')
    condition = models.TextField(blank=True, help_text="JSON condition for when this applies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['role', 'content_type', 'field_name']

    def __str__(self):
        return f"{self.role.name} - {self.field_name} ({self.access_level})"

class RecordPermission(models.Model):
    ACCESS_CHOICES = [
        ('none', 'No Access'),
        ('view', 'View Only'),
        ('edit', 'View & Edit'),
        ('delete', 'Full Access'),
    ]

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='record_permissions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='view')
    filter_condition = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['role', 'content_type']

    def __str__(self):
        return f"{self.role.name} - {self.content_type.model} ({self.access_level})"

class PermissionAudit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='permission_audits')
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=100)
    resource_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
