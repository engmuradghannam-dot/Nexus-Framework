"""PMO Signals"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project, Portfolio


@receiver(post_save, sender=Project)
def project_post_save(sender, instance, created, **kwargs):
    """Handle project post-save actions"""
    if created:
        pass


@receiver(post_delete, sender=Project)
def project_post_delete(sender, instance, **kwargs):
    """Handle project post-delete cleanup"""
    pass


@receiver(post_save, sender=Portfolio)
def portfolio_post_save(sender, instance, created, **kwargs):
    """Handle portfolio post-save actions"""
    if created:
        pass


@receiver(post_delete, sender=Portfolio)
def portfolio_post_delete(sender, instance, **kwargs):
    """Handle portfolio post-delete cleanup"""
    pass
