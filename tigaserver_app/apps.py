from django.apps import AppConfig
from django.conf import settings

from timezonefinder import TimezoneFinder
from pyfcm import FCMNotification

class TigaserverApp(AppConfig):
    name = "tigaserver_app"
    label = "tigaserver_app"
    verbose_name = "Tigaserver_App"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()
        self.push_service = FCMNotification(api_key=settings.FCM_API_KEY) if settings.FCM_API_KEY else None
