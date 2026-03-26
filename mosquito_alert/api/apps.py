from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "mosquito_alert.api"
    label = "api"

    def ready(self) -> None:
        pass
