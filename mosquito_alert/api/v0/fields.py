from rest_framework import serializers


class NullableTimeZoneDatetimeField(serializers.DateTimeField):
    def enforce_timezone(self, value):
        return value


class AutoTimeZoneDatetimeField(NullableTimeZoneDatetimeField):
    # NOTE: to be used when inheriting AutoTimeZoneSerializerMixin
    pass
