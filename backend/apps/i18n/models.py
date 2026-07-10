import uuid

from django.db import models


class Language(models.Model):
    DIRECTION_CHOICES = [
        ("ltr", "Left-to-Right"),
        ("rtl", "Right-to-Left"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, db_index=True, help_text="ISO 639-1 code + optional region")
    name = models.CharField(max_length=100)
    name_local = models.CharField(max_length=100, help_text="Native name")
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES, default="ltr")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    flag_emoji = models.CharField(max_length=10, blank=True)
    decimal_separator = models.CharField(max_length=5, default=".")
    thousands_separator = models.CharField(max_length=5, default=",")
    date_format = models.CharField(max_length=50, default="YYYY-MM-DD")
    time_format = models.CharField(max_length=50, default="HH:mm")
    first_day_of_week = models.PositiveSmallIntegerField(default=1, help_text="1=Monday, 7=Sunday")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Language.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Translation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="translations"
    )
    key = models.CharField(max_length=500, db_index=True)
    value = models.TextField()
    context = models.CharField(max_length=200, blank=True, db_index=True, help_text="Module or page context")
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.CharField(max_length=100, blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key", "language"]
        verbose_name = "Translation"
        verbose_name_plural = "Translations"
        unique_together = [["language", "key", "context"]]
        indexes = [
            models.Index(fields=["key", "language"]),
            models.Index(fields=["context", "language"]),
        ]

    def __str__(self):
        return f"{self.key} ({self.language.code})"


class TranslationImportJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to="translation_imports/")
    language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name="import_jobs"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    error_log = models.JSONField(default=list)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Translation Import Job"
        verbose_name_plural = "Translation Import Jobs"

    def __str__(self):
        return f"{self.name} ({self.status})"
