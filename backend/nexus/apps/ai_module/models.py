from django.core.validators import MinLengthValidator
from django.db import models
from django.contrib.auth.models import User

class AIModel(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    provider = models.CharField(max_length=100)
    model_id = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"

class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations', db_constraint=False)
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Untitled'}"

class AIMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

class AIPromptTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    system_prompt = models.TextField()
    user_template = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
