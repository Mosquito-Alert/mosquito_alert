from corsheaders.defaults import default_headers
import firebase_admin

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}

# FIREBASE
# ------------------------
FIREBASE_APP = None
if env("GOOGLE_APPLICATION_CREDENTIALS", default=None):
    FIREBASE_APP = firebase_admin.initialize_app()

# For sentry_sdk
if env("SENTRY_DSN", default=None):
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        traces_sample_rate=1.0,
        integrations=[
            DjangoIntegration(cache_spans=True),
        ],
    )

    # django-cors-headers - https://github.com/adamchainz/django-cors-headers#setup
    # -------------------------------------------------------------------------------
    CORS_ALLOW_HEADERS = (
        *default_headers,
        "sentry-trace",
        "baggage",
    )
