"""
Auto-create superuser on startup
by @eng.Murad Alhassan
"""
from django.core.management.base import BaseCommand
from apps.core.models import User


class Command(BaseCommand):
    help = 'Initialize default superuser'

    def handle(self, *args, **options):
        email = 'eng.murad.ghannam@gmail.com'
        password = 'ghannam2020'

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Murad',
                'last_name': 'Alhassan',
                'is_superuser': True,
                'is_staff': True,
                'is_active': True,
            }
        )

        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{email}" created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{email}" updated successfully!'))
