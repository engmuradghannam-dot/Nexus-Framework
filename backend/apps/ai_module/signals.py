from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AIInsight


@receiver(post_save, sender=AIInsight)
def handle_insight_save(sender, instance, created, **kwargs):
    if created:
        pass
