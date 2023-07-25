from django.apps import AppConfig
from flag.apps import FlagConfig as OriginalFlagConfig


class FlagConfig(OriginalFlagConfig):
    # Overriding FlagConfig to avoid extra migrations when running makemigrations.
    default_auto_field = "django.db.models.AutoField"


class ModerationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mosquito_alert.moderation"
