from rest_framework import serializers

from drf_spectacular.authentication import SessionScheme
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme, TokenObtainPairSerializerExtension
from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import inline_serializer, extend_schema, extend_schema_view

from ..error_serializers import ErrorResponse401Serializer


class TokenViewBase(OpenApiViewExtension):
    target_class = 'rest_framework_simplejwt.views.TokenViewBase'
    match_subclasses = True

    def view_replacement(self):
        response_serializer = self.target().get_serializer_class()

        return extend_schema_view(
            post=extend_schema(responses={
                200: response_serializer,
                401: ErrorResponse401Serializer,
            })
        )(self.target)

class AppUserJWTAuthentication(SimpleJWTScheme):
    target_class = "api.auth.authentication.AppUserJWTAuthentication"

class AppUserTokenObtainPairSerializer(TokenObtainPairSerializerExtension):
    target_class = "api.auth.serializers.AppUserTokenObtainPairSerializer"

    def map_serializer(self, auto_schema, direction):
        Fixed = inline_serializer('Fixed', fields={
            'username': serializers.CharField(write_only=True),
            'password': serializers.CharField(write_only=True),
            'device_id': serializers.CharField(write_only=True, required=False),
            'access': serializers.CharField(read_only=True),
            'refresh': serializers.CharField(read_only=True),
        })
        return auto_schema._map_serializer(Fixed, direction)

class NonAppUserSessionAuthentication(SessionScheme):
    target_class = "api.auth.authentication.NonAppUserSessionAuthentication"