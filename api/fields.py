import inspect
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field
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
        EXCLUDED_PREFIXES = ("SystemV/", "Factory", "localtime")
        _tzstrs = {
            tz
            for tz in zoneinfo.available_timezones()
            if not tz.startswith(EXCLUDED_PREFIXES)
        }
        super().__init__(choices=sorted(_tzstrs), use_pytz=False, html_cutoff=5, **kwargs)


class WritableSerializerMethodField(serializers.Field):
    # Reference: https://stackoverflow.com/a/64274128/8450576
    def __init__(self, field_class, method_name=None, **kwargs):
        self._deserializer_source = kwargs.pop('source', None)
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
        self.deserializer_field.bind(self._deserializer_source or field_name, parent)
        return ret

    def run_validation(self, *args, **kwargs):
        return {
            self.deserializer_field.field_name: self.deserializer_field.run_validation(*args, **kwargs)
        }

    def to_internal_value(self, data):
        return {
            self.deserializer_field.field_name: self.deserializer_field.to_internal_value(data=data)
        }

    def to_representation(self, value):
        return self.serializer_field.to_representation(value=value)


@extend_schema_field({
    "type": "string",
    "format": "html",
    "example": "<body><p><strong>Welcome!</strong>this is a text in html.</p></body>"
})
class HTMLCharField(serializers.CharField):
    """
    A CharField that represents HTML content.
    """
    pass