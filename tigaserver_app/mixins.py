from abc import abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta, tzinfo, timezone as dt_timezone
import pytz
from typing import Union

from django.apps import apps
from django.db import models
from django.utils import timezone

from .apps import TigaserverApp
from .fields import AutoTimeZoneDatetimeField
from .utils import is_instant_upload_candidate, apply_tz_to_datetime


class TimeZoneModelMixin(models.Model):
    @abstractmethod
    def _get_latitude_for_timezone(self) -> Union[float, None]:
        raise NotImplementedError

    @abstractmethod
    def _get_longitude_for_timezone(self) -> Union[float, None]:
        raise NotImplementedError

    def get_timezone_from_coordinates(self) -> Union[tzinfo, None]:
        latitude = self._get_latitude_for_timezone()
        longitude = self._get_longitude_for_timezone()

        timezone_from_coordinates = None
        if latitude is not None and longitude is not None:
            tf = apps.get_app_config(app_label=TigaserverApp.label).timezone_finder

            # Get the timezone based on latitude and longitude
            try:
                timezone_from_coordinates = pytz.timezone(
                    tf.timezone_at(lat=latitude, lng=longitude)
                )
            except ValueError:
                # Timezonefinder: the coordinates were out of bounds
                pass
            except pytz.exceptions.UnknownTimeZoneError:
                pass

        return timezone_from_coordinates

    class Meta:
        abstract = True


class AutoTimeZoneSerializerMixin(object):
    def _get_dict_applied_tz(self, data: OrderedDict, tz: pytz.timezone) -> OrderedDict:
        # Apply the Timezone to all fields that still not have a timezone set and
        # cast to the default timezone.
        # Return only the fields where the process has been applied.
        data_result = OrderedDict()
        for datetime_fieldname in self._get_fields_to_apply_tz(data=data):
            data_result[datetime_fieldname] = apply_tz_to_datetime(
                data[datetime_fieldname], tz=tz
            ).astimezone(timezone.get_default_timezone())

        return data_result

    def _get_auto_tz_datetime_fields(self) -> list:
        field_names = []
        for field_name, field_instance in self.fields.items():
            if isinstance(field_instance, AutoTimeZoneDatetimeField):
                field_names.append(field_name)
        return field_names

    def _get_fields_to_apply_tz(self, data: OrderedDict) -> list:
        # Only return those AutoTimeZone field without a Timezone defined.
        return list(
            filter(
                lambda x: not timezone.is_aware(data[x]),
                self._get_auto_tz_datetime_fields(),
            )
        )

    def to_internal_value(self, data: OrderedDict) -> OrderedDict:
        data = super().to_internal_value(data)

        if self.instance:
            # If not running on create, exit.
            return data

        # Getting the Timezone using the location.
        model = self.Meta.model
        timezone_from_coordinates = model(
            **{
                key: value
                for key, value in data.items()
                if key in [x.name for x in model._meta.local_fields]
            }
        ).get_timezone_from_coordinates()

        data = OrderedDict({
            **data,
            **self._get_dict_applied_tz(data=data, tz=timezone_from_coordinates),
        })
        # Ensure all AutoTimeZoneDatetimeField are aware
        for fname in self._get_auto_tz_datetime_fields():
            if not timezone.is_aware(data[fname]):
                data[fname] = apply_tz_to_datetime(data[fname], tz=timezone.get_default_timezone())

        return data


class AutoTimeZoneOrInstantUploadSerializerMixin(AutoTimeZoneSerializerMixin):
    @property
    @abstractmethod
    def CLIENT_CREATION_FIELD(self):
        raise NotImplementedError

    def _get_fields_to_apply_tz_from_instant_upload(self, data: OrderedDict) -> list:
        return self._get_fields_to_apply_tz(data=data)

    def _get_dict_applied_tz(self, data: OrderedDict, tz: pytz.timezone) -> OrderedDict:
        # First, get the result from the location timezone approach.
        data_result = super()._get_dict_applied_tz(data, tz)

        tmp_data = OrderedDict({**data, **data_result})
        if tmp_data[self.CLIENT_CREATION_FIELD] is None:
            return data_result

        # Get current client creation time and make sure is aware of timezone.
        _client_creation_time_fix_coordiantes = tmp_data[self.CLIENT_CREATION_FIELD]
        if not timezone.is_aware(_client_creation_time_fix_coordiantes):
            _client_creation_time_fix_coordiantes = apply_tz_to_datetime(
                _client_creation_time_fix_coordiantes, tz=timezone.get_default_timezone()
            )

        # Original creation field
        _client_creation_field = data[self.CLIENT_CREATION_FIELD]
        if not timezone.is_aware(_client_creation_field):
            # If does not contain TZ, use the default timezone
            _client_creation_field = apply_tz_to_datetime(
                _client_creation_field, tz=timezone.get_default_timezone()
            )

        now = datetime.now(timezone.get_default_timezone())
        # If after applying the Timezone obtained from cooridinates,
        # the upload is still high (>15min)
        upload_elapsed_seconds = (
            now - _client_creation_time_fix_coordiantes
        ).total_seconds()
        if abs(upload_elapsed_seconds) > 15 * 60:
            # 2. If consider to be an instant upload.
            if is_instant_upload_candidate(
                server_creation_datetime=now,
                user_creation_datetime=_client_creation_time_fix_coordiantes,
            ):
                interval_minutes = 15  # nearest 15min interval
                try:
                    timedelta_factor = timedelta(
                        minutes=round(
                            (
                                _client_creation_field - now
                            ).total_seconds() / 60 / interval_minutes
                        ) * interval_minutes
                    )
                except ValueError:
                    # case offset greater than 1day.
                    timedelta_factor = timedelta(seconds=0)

                for (
                    datetime_fieldname
                ) in self._get_fields_to_apply_tz_from_instant_upload(data=data):
                    _primitive_datetime_fieldname = data[datetime_fieldname]
                    if not timezone.is_naive(_primitive_datetime_fieldname):
                        _primitive_datetime_fieldname = timezone.make_naive(_primitive_datetime_fieldname)

                    data_result[datetime_fieldname] = apply_tz_to_datetime(
                            value=_primitive_datetime_fieldname,
                            tz=dt_timezone(offset=timedelta_factor)
                        )

        return data_result
