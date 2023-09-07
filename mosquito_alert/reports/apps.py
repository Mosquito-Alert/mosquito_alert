from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.reports"

    def ready(self) -> None:
        import mosquito_alert.reports.signals  # noqa: F401
