from django.apps import AppConfig


class PizzaManagementConfig(AppConfig):
    name = 'pizza_management'
    
    def ready(self):
        # Import signals when Django app is ready
        import pizza_management.signals  # noqa