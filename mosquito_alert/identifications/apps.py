from django.apps import AppConfig


class IdentificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.identifications"

    def ready(self) -> None:
        import mosquito_alert.identifications.signals  # noqa: F401