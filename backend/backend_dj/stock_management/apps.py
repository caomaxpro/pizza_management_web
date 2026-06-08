from django.apps import AppConfig


class StockManagementConfig(AppConfig):
    name = 'stock_management'

    def ready(self):
        import stock_management.inventory.signals  # noqa: F401 – register signals
