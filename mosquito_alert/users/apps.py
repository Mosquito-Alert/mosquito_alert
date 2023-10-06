from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "mosquito_alert.users"
    verbose_name = _("Users")

    def ready(self):
        import mosquito_alert.users.signals  # noqa: F401
