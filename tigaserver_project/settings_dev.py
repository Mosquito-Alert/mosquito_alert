from .settings import *

DEBUG = True
TEMPLATE_DEBUG = True

# See docker-compose service.
DATABASES["default"] = {
    "ENGINE": "django.contrib.gis.db.backends.postgis",
    "NAME": "postgres",
    "USER": "postgres",
    "PASSWORD": "postgres",
    "HOST": "postgres",
    "PORT": "5432",
}

CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "",
}

DISABLE_PUSH_IOS = True
DISABLE_PUSH_ANDROID = True
DRY_RUN_PUSH = False
DISABLE_ACHIEVEMENT_NOTIFICATIONS = False

HOST_NAME = "localhost"
SITE_URL = "http://localhost:8000/static/tigapublic/"
TIGASERVER_API = "http://localhost:8000/api/"

SITE_ID = 1

TIGASERVER_API = "development"
