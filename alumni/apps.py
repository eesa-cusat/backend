from django.apps import AppConfig


class AlumniConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alumni'
    verbose_name = 'Alumni Management'
    
    def ready(self):
        # Import signals here if needed
        pass
