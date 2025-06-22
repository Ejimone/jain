from django.apps import AppConfig


class StudentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student'
    verbose_name = 'Student Management'

    def ready(self):
        """Import signal handlers when app is ready"""
        try:
            import student.signals  # noqa F401
        except ImportError:
            pass
