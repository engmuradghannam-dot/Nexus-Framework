from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project, Portfolio


@receiver(post_save, sender=Project)
def handle_project_save(sender, instance, created, **kwargs):
    if created and instance.portfolio:
        portfolio = instance.portfolio
        portfolio.project_count = Project.objects.filter(portfolio=portfolio).count()
        portfolio.save(update_fields=['project_count'])


@receiver(post_delete, sender=Project)
def handle_project_delete(sender, instance, **kwargs):
    if instance.portfolio:
        portfolio = instance.portfolio
        portfolio.project_count = Project.objects.filter(portfolio=portfolio).count()
        portfolio.save(update_fields=['project_count'])
