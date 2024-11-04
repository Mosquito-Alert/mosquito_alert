from django.contrib.auth import authenticate

from rest_framework import exceptions, serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    TokenObtainPairSerializer,
)


class AppUserTokenObtainSerializer(TokenObtainSerializer):
    uuid = serializers.UUIDField(write_only=True, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        del self.fields[self.username_field]

    def validate(self, attrs):
        authenticate_kwargs = {
            "uuid": attrs["uuid"],
            "password": attrs["password"],  # or None,
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
