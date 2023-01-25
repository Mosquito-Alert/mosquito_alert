from django.apps import AppConfig


class TaxaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.taxa"

    def ready(self) -> None:
        import mosquito_alert.taxa.signals  # noqa: F401
