from django.apps import AppConfig


class WorkspacesConfig(AppConfig):
    name = "mosquito_alert.workspaces"

    def ready(self) -> None:
        import mosquito_alert.workspaces.signals  # noqa: F401
