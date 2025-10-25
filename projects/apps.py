from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    verbose_name = 'Project Administration'
    
    def ready(self):
        """Import signals when app is ready"""
        import projects.signals  # noqa
