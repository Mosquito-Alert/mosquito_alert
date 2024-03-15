import pytz

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from rest_framework import serializers

from drf_extra_fields.geo_fields import PointField
from timezone_field.utils import use_pytz_default
from timezone_field.rest_framework import TimeZoneSerializerField


class TimezoneAwareDateTimeField(serializers.DateTimeField):
    def to_internal_value(self, value):
        # Parse the datetime string into a datetime object
        parsed_dt = parse_datetime(value)

        # Ensure that the datetime contains timezone information
        if parsed_dt.tzinfo is None:
            raise ValidationError("Datetime value must include timezone information.")

        return super().to_internal_value(value=value)


class ExpandedPointField(PointField):
    def __init__(self, *args, **kwargs):
        super().__init__(str_points=True, *args, **kwargs)


class IntegerDefaultField(serializers.IntegerField):
    # When db value is None, use the default.
    def get_attribute(self, instance):
        attibute = super().get_attribute(instance)
        if attibute is None and self.default != serializers.empty:
            attibute = self.default
        return attibute


class TimeZoneSerializerChoiceField(TimeZoneSerializerField, serializers.ChoiceField):
    def __init__(self, **kwargs):
        self.use_pytz = kwargs.pop("use_pytz", use_pytz_default())

        _tzstrs = (
            pytz.common_timezones if self.use_pytz else zoneinfo.available_timezones()
        )

        super().__init__(choices=_tzstrs, html_cutoff=5, **kwargs)


class WritableSerializerMethodField(serializers.SerializerMethodField):
    # Reference: https://stackoverflow.com/a/64274128/8450576
    def __init__(self, **kwargs):
        self.setter_method_name = kwargs.pop("setter_method_name", None)
        self.deserializer_field = kwargs.pop("deserializer_field")

        super().__init__(**kwargs)

        self.read_only = False
        self.required = True

    def bind(self, field_name, parent):
        retval = super().bind(field_name, parent)
        if not self.setter_method_name:
            self.setter_method_name = f"set_{field_name}"

        return retval

    def get_default(self):
        default = super().get_default()

        return {self.field_name: default}

    def to_internal_value(self, data):
        value = self.deserializer_field.to_internal_value(data)
        method = getattr(self.parent, self.setter_method_name)
        return {
            self.field_name: self.deserializer_field.to_internal_value(method(value))
        }
