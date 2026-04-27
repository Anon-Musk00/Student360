from django.core.management.base import BaseCommand
from student.models import Admin

class Command(BaseCommand):
    help = 'Create initial primary admin account'

    def handle(self, *args, **options):
        admin, created = Admin.objects.get_or_create(
            username='admin@123',
            defaults={
                'email': 'admin@school.edu',
                'password': 'admin123',
                'role': 'primary',
                'status': 'active'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created primary admin: {admin.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Primary admin already exists: {admin.username} ({admin.role})')
            )
