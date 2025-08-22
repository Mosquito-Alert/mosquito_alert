from typing import Optional, Union

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from rest_framework import exceptions, serializers
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    TokenObtainPairSerializer,
    PasswordField
)

from tigaserver_app.models import TigaUser, Device

from .tokens import RefreshToken

User = get_user_model()

class AppUserTokenObtainSerializer(TokenObtainSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device_id"] = serializers.CharField(required=False, write_only=True)

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            "uuid": attrs[self.username_field],
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

        self.device = None
        if isinstance(self.user, TigaUser) and attrs.get("device_id"):
            self.device, _ = Device.objects.get_or_create(
                device_id=attrs["device_id"],
                user=self.user
            )

        return {}


class AppUserTokenObtainPairSerializer(
    TokenObtainPairSerializer, AppUserTokenObtainSerializer
):

    token_class = RefreshToken

    @classmethod
    def get_token(cls, user: Union[TigaUser, 'User'], device_id: Optional[str] = None) -> Token:
        token = super().get_token(user)

        if isinstance(user, TigaUser) and device_id:
            # Add custom claims to the JWT token
            token['device_id'] = device_id

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if isinstance(self.user, TigaUser) and self.device:
            # Recreate token passing now device_id
            refresh =  self.get_token(user=self.user, device_id=self.device.device_id)
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)

            self.device.active_session = True
            # NOTE: adding 'active' in the update_fields is important.
            #       The save() method will trigger active = False depending on the value of active_session.
            _update_fields=["active_session", "active"]
            # Update last_login device
            if api_settings.UPDATE_LAST_LOGIN:
                self.device.last_login = timezone.now()
                _update_fields.append("last_login")

            self.device.save(update_fields=_update_fields)

        return data


class GuestRegistrationSerializer(serializers.ModelSerializer):
    # Using rest_framework_simplejwt not to have problems when
    # getting the JWT Token
    password = PasswordField(
        min_length=8,
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        instance = super().create(validated_data)
        instance.set_password(raw_password)
        instance.save()
        return instance

    class Meta:
        model = TigaUser
        fields = (
            "username",
            "password",
        )
        read_only_fields = (
            "username",
        )
        extra_kwargs = {
            "username": {"source": "user_UUID"},
        }

class PasswordChangeSerializer(serializers.ModelSerializer):
    # Using rest_framework_simplejwt not to have problems when
    # getting the JWT Token
    password = PasswordField(
        min_length=8,
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = TigaUser
        fields = ('password',)