from django.db import models

from rest_framework import serializers

from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from drf_standardized_errors.openapi_serializers import ClientErrorEnum, ErrorCode401Enum as OriginalErrorCode401Enum


class ErrorCode401Enum(models.TextChoices):
    INVALID_TOKEN = InvalidToken.default_code
    AUTHENTICATION_FAILED = AuthenticationFailed.default_code
    # From the original ErrorCode401Enum
    NOT_AUTHENTICATED = OriginalErrorCode401Enum.NOT_AUTHENTICATED


class Error401Serializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=ErrorCode401Enum.choices)
    detail = serializers.CharField()
    attr = serializers.CharField(allow_null=True)


class ErrorResponse401Serializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    errors = Error401Serializer(many=True)