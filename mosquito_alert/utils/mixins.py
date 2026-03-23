from abc import abstractmethod
from typing import Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.apps import apps
from django.db import models

from .apps import UtilsApp


class TimeZoneModelMixin(models.Model):
    @abstractmethod
    def _get_latitude_for_timezone(self) -> Union[float, None]:
        raise NotImplementedError

    @abstractmethod
    def _get_longitude_for_timezone(self) -> Union[float, None]:
        raise NotImplementedError

    def get_timezone_from_coordinates(self) -> Union[ZoneInfo, None]:
        latitude = self._get_latitude_for_timezone()
        longitude = self._get_longitude_for_timezone()

        timezone_from_coordinates = None
        if latitude is not None and longitude is not None:
            tf = apps.get_app_config(app_label=UtilsApp.label).timezone_finder

            # Get the timezone based on latitude and longitude
            try:
                timezone_from_coordinates = ZoneInfo(
                    tf.timezone_at(lat=latitude, lng=longitude)
                )
            except ValueError:
                # Timezonefinder: the coordinates were out of bounds
                pass
            except ZoneInfoNotFoundError:
                pass

        return timezone_from_coordinates

    class Meta:
        abstract = True

