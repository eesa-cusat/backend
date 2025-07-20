from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial superuser for deployment (no SSH access)'

    def handle(self, *args, **options):
        # Simple default credentials for initial setup
        username = 'admin'
        email = 'admin@eesa.com'
        password = 'eesa2024'  # Simple password that can be changed later
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists - skipping creation')
            )
            return
        
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Initial superuser created successfully!')
            )
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🔑 Username: {username}')
            self.stdout.write(f'🔐 Password: {password}')
            self.stdout.write(
                self.style.WARNING('⚠️  IMPORTANT: Change password after first login via /eesa/')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating superuser: {str(e)}')
            )
