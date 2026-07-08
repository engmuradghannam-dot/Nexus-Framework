from django.db import models
from django.conf import settings
import uuid


class AIModel(models.Model):
    STATUS_CHOICES = [
        ('training', 'Training'),
        ('ready', 'Ready'),
        ('deployed', 'Deployed'),
        ('deprecated', 'Deprecated'),
    ]
    MODEL_TYPES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
        ('nlp', 'NLP'),
        ('cv', 'Computer Vision'),
        ('forecasting', 'Forecasting'),
        ('anomaly', 'Anomaly Detection'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='training')
    description = models.TextField(blank=True)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    f1_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    training_data_size = models.PositiveBigIntegerField(default=0)
    last_trained = models.DateTimeField(null=True, blank=True)
    deployed_at = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='ai_models'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_models'
        ordering = ['-created_at']
        unique_together = ['name', 'version']

    def __str__(self):
        return f"{self.name} v{self.version}"


class Prediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='predictions')
    input_data = models.JSONField()
    output_data = models.JSONField()
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction by {self.model.name} ({self.confidence})"


class Insight(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    source_model = models.ForeignKey(
        AIModel, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='insights'
    )
    related_project = models.ForeignKey(
        'pmo.Project', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ai_insights'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_insights'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
