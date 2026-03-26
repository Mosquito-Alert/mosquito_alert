from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "mosquito_alert.api"
    label = "api"

    def ready(self) -> None:
        import mosquito_alert.api.v1.schema  # noqa: F401
        import mosquito_alert.api.v1.auth.schema  # noqa: F401
