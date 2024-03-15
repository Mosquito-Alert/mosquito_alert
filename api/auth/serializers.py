from django.contrib.auth import authenticate

from rest_framework import exceptions, serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    TokenObtainPairSerializer,
)


class AppUserTokenObtainSerializer(TokenObtainSerializer):
    uuid = serializers.UUIDField(required=True)
    device_token = serializers.CharField(allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        del self.fields[self.username_field]
        del self.fields["password"]

    def validate(self, attrs):
        authenticate_kwargs = {
            "uuid": attrs["uuid"],
            "device_token": attrs["device_token"],  # or None,
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}


class AppUserTokenObtainPairSerializer(
    TokenObtainPairSerializer, AppUserTokenObtainSerializer
):
    pass
