from django.apps import AppConfig
from django.conf import settings

import firebase_admin
from firebase_admin.credentials import Certificate
from timezonefinder import TimezoneFinder

from .pillow_utils import register_raw_opener
from pillow_heif import register_heif_opener

register_heif_opener()
register_raw_opener()


class TigaserverApp(AppConfig):
    name = "tigaserver_app"
    label = "tigaserver_app"
    verbose_name = "Tigaserver_App"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()

        # Initialize firebase app
        if settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIAL:
            firebase_app = firebase_admin.initialize_app(
                credential=Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIAL)
            )