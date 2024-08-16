from django.apps import AppConfig
from django.conf import settings

import firebase_admin
from firebase_admin.credentials import Certificate
from timezonefinder import TimezoneFinder

class TigaserverApp(AppConfig):
    name = "tigaserver_app"
    label = "tigaserver_app"
    verbose_name = "Tigaserver_App"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()
        self.push_service = FCMNotification(api_key=settings.FCM_API_KEY) if settings.FCM_API_KEY else None

        # Initialize firebase app
        if settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIAL:
            firebase_app = firebase_admin.initialize_app(
                credential=Certificate(settings.FIREBASE_SERVICE_ACCOUNT_CREDENTIAL)
            )