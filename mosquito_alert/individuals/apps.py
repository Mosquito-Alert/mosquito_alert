from django.apps import AppConfig


class IndividualsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.individuals"

    def ready(self) -> None:
        import mosquito_alert.individuals.signals  # noqa: F401
