from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "api"
    label = "api"

    def ready(self) -> None:
        import api.schema
        import api.auth.schema
