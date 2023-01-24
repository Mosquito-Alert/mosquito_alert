from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.notifications"
    label = "platform_notifications"

    def ready(self) -> None:
        import mosquito_alert.notifications.signals  # noqa: F401
