from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model
from django.dispatch import receiver

User = get_user_model()

@receiver(post_migrate)
def create_initial_superuser(sender, **kwargs):
    """
    Create initial superuser automatically after migrations
    Only runs once for the accounts app
    """
    if sender.name == 'accounts':
        username = 'admin'
        email = 'admin@eesa.com'
        password = 'admin123'
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f'✅ Initial superuser created: {username}')
            print(f'📧 Email: {email}')
            print(f'🔑 Password: {password}')
            print('⚠️  IMPORTANT: Change password after first login via /eesa/')
