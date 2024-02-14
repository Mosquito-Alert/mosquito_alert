from django.apps import AppConfig
from timezonefinder import TimezoneFinder


class TigaserverApp(AppConfig):
    name = "tigaserver_app"
    label = "tigaserver_app"
    verbose_name = "Tigaserver_App"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()
