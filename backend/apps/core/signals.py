"""
Core Signals - Auto-create superuser and handle post-save operations
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Handle post-save operations for users."""
    if created:
        # Any additional setup for new users can go here
        pass
