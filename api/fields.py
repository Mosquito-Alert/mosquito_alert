import inspect
import pytz
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from rest_framework import serializers

from taggit.serializers import TagListSerializerField as OriginalTagListSerializerField
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
        # NOTE: We need to use pytz.all_timezones instead of pytz.common_timezones since
        #       this is not manually set, but set automatically depending on the lat/lon.
        _tzstrs = (
            pytz.all_timezones if self.use_pytz else zoneinfo.available_timezones()
        )
        super().__init__(choices=sorted(_tzstrs), html_cutoff=5, **kwargs)


class WritableSerializerMethodField(serializers.Field):
    # Reference: https://stackoverflow.com/a/64274128/8450576
    def __init__(self, field_class, method_name=None, **kwargs):
        self.deserializer_field = field_class(**kwargs)

        self.serializer_field = serializers.SerializerMethodField(
            method_name=method_name,
        )

        allowed_keys = [
            param for param in inspect.signature(serializers.Field.__init__).parameters if param != 'self'
        ]
        kwargs = {key: value for key, value in kwargs.items() if key in allowed_keys}

        kwargs['source'] = '*'
        kwargs['read_only'] = False

        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        ret = super().bind(field_name, parent)
        self.serializer_field.bind(field_name, parent)
        self.deserializer_field.bind(field_name, parent)
        return ret

    def run_validation(self, *args, **kwargs):
        return {
            self.field_name: self.deserializer_field.run_validation(*args, **kwargs)
        }

    def to_internal_value(self, data):
        return {
            self.field_name: self.deserializer_field.to_internal_value(data=data)
        }

    def to_representation(self, value):
        return self.serializer_field.to_representation(value=value)


class TagListSerializerField(OriginalTagListSerializerField, serializers.ListField):
    # NOTE: the current django-taggit version uses CharField, which introduces an error 
    # on POST, getting char instead of a list of element.
    pass
