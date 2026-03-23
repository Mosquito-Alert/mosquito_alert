from django.apps import AppConfig

from timezonefinder import TimezoneFinder


class UtilsApp(AppConfig):
    name = "mosquito_alert.utils"
    label = "utils"
    verbose_name = "Utils"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()