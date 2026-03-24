from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "mosquito_alert.notifications"

    def ready(self) -> None:
        import mosquito_alert.notifications.signals  # noqa: F401