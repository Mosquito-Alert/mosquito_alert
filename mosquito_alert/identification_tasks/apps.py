from django.apps import AppConfig


class IdentificationTasksConfig(AppConfig):
    name = "mosquito_alert.identification_tasks"

    def ready(self) -> None:
        import mosquito_alert.identification_tasks.signals  # noqa: F401
