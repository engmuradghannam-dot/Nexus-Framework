from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ChangeHeader(models.Model):
    """SAP CDHDR-equivalent: one row per change transaction on a business object."""

    CHANGE_TYPE_CHOICES = [('I', 'Insert'), ('U', 'Update'), ('D', 'Delete')]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    object_id = models.CharField(max_length=50)
    target = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=200, blank=True)
    change_type = models.CharField(max_length=1, choices=CHANGE_TYPE_CHOICES)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    username_snapshot = models.CharField(max_length=150, default='system')
    change_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-change_time']
        indexes = [models.Index(fields=['content_type', 'object_id'])]
        verbose_name = 'Change Header (CDHDR)'

    def __str__(self):
        return f"{self.content_type.model} #{self.object_id} [{self.change_type}] @ {self.change_time:%Y-%m-%d %H:%M}"


class ChangeItem(models.Model):
    """SAP CDPOS-equivalent: one row per changed field within a ChangeHeader."""

    CHANGE_INDICATOR_CHOICES = [('I', 'Insert'), ('U', 'Update'), ('D', 'Delete')]

    header = models.ForeignKey(ChangeHeader, on_delete=models.CASCADE, related_name='items')
    field_name = models.CharField(max_length=100)
    change_indicator = models.CharField(max_length=1, choices=CHANGE_INDICATOR_CHOICES)
    value_old = models.TextField(blank=True)
    value_new = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Change Item (CDPOS)'

    def __str__(self):
        return f"{self.header_id} - {self.field_name}: {self.value_old!r} -> {self.value_new!r}"
