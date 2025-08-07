from django.db.models.signals import post_migrate, m2m_changed
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


@receiver(m2m_changed, sender=User.groups.through)
def update_staff_status(sender, **kwargs):
    """
    Update user's is_staff status when groups change
    """
    if kwargs['action'] in ['post_add', 'post_remove', 'post_clear']:
        user = kwargs['instance']
        # Set is_staff to True if user has any groups, False otherwise
        user.is_staff = user.is_superuser or user.groups.exists()
        # Use update to avoid triggering save signals
        User.objects.filter(pk=user.pk).update(is_staff=user.is_staff)
