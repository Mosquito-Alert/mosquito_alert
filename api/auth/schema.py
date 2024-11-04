from rest_framework import serializers

from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme, TokenObtainPairSerializerExtension
from drf_spectacular.utils import inline_serializer


class AppUserJWTAuthentication(SimpleJWTScheme):
    target_class = "api.auth.authentication.AppUserJWTAuthentication"

class AppUserTokenObtainPairSerializer(TokenObtainPairSerializerExtension):
    target_class = "api.auth.serializers.AppUserTokenObtainPairSerializer"

    def map_serializer(self, auto_schema, direction):
        Fixed = inline_serializer('Fixed', fields={
            'uuid': serializers.UUIDField(write_only=True),
            'password': serializers.CharField(write_only=True),
            'access': serializers.CharField(read_only=True),
            'refresh': serializers.CharField(read_only=True),
        })
        return auto_schema._map_serializer(Fixed, direction)
