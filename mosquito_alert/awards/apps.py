from django.apps import AppConfig


class AwardsConfig(AppConfig):
    name = "mosquito_alert.awards"

    def ready(self) -> None:
        import mosquito_alert.awards.signals  # noqa: F401
