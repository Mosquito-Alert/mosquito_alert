from .settings import *

DATABASES["donete"] = {
    # Using defaults according to CI configuration.
    # Will be replaced when importing the settings_local
    "ENGINE": "django.contrib.gis.db.backends.postgis",
    "NAME": "postgres",
    "USER": "postgres",
    "PASSWORD": "postgres",
    "HOST": "postgres_donete",  # See docker-compose service.
    "PORT": "5432",
}

# Disable PUSH notifications
DISABLE_PUSH_IOS = True
DISABLE_PUSH_ANDROID = True
DRY_RUN_PUSH = False
