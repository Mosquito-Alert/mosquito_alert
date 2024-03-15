from django.db.models import Model
from django.core.exceptions import ImproperlyConfigured

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty


class FieldPolymorphicSerializer(serializers.Serializer):
    field_value_serializer_mapping = None
    resource_type_field_name = "type"
    model = None

    def __new__(cls, *args, **kwargs):
        if cls.field_value_serializer_mapping is None:
            raise ImproperlyConfigured(
                "`{cls}` is missing a "
                "`{cls}.field_value_serializer_mapping` attribute".format(
                    cls=cls.__name__
                )
            )
        if not isinstance(cls.resource_type_field_name, str):
            raise ImproperlyConfigured(
                "`{cls}.resource_type_field_name` must be a string".format(
                    cls=cls.__name__
                )
            )
        if not issubclass(cls.model, Model):
            raise ImproperlyConfigured(
                "`{cls}.model` must be a django Model".format(cls=cls.__name__)
            )
        return super().__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field_value_serializer_mapping = self.field_value_serializer_mapping
        self.field_value_serializer_mapping = {}
        for field_value, serializer in field_value_serializer_mapping.items():
            if callable(serializer):
                serializer = serializer(*args, **kwargs)
                serializer.parent = self

            self.field_value_serializer_mapping[field_value] = serializer

    def to_representation(self, instance):
        serializer = self._get_serializer_for_instance(instance=instance)
        return serializer.to_representation(instance)

    def to_internal_value(self, data):
        if self.instance:
            serializer = self._get_serializer_for_instance(instance=self.instance)
        else:
            serializer = self._get_serializer_for_data(data=data)
        return serializer.to_internal_value(data=data)

    def create(self, validated_data):
        serializer = self._get_serializer_for_data(data=validated_data)
        return serializer.create(validated_data)

    def update(self, instance, validated_data):
        serializer = self._get_serializer_for_data(data=validated_data)
        return serializer.update(instance, validated_data)

    def is_valid(self, raise_exception=False):
        valid = super().is_valid(raise_exception)

        try:
            if self.instance:
                serializer = self._get_serializer_for_instance(instance=self.instance)
            else:
                serializer = self._get_serializer_for_data(data=self.initial_data)
        except ValidationError:
            child_valid = False
        else:
            child_valid = serializer.is_valid(raise_exception)
            self._errors.update(serializer.errors)

        return valid and child_valid

    def run_validation(self, data=empty):
        if self.instance:
            serializer = self._get_serializer_for_instance(instance=self.instance)
        else:
            serializer = self._get_serializer_for_data(data=data)
        return serializer.run_validation(data)

    def _get_serializer_for_type(self, type_value):
        try:
            return self.field_value_serializer_mapping[type_value]
        except KeyError:
            raise ValidationError(
                f"Value {type_value} has not serializer assigned for field '{self.resource_type_field_name}'"
            )

    def _get_serializer_for_instance(self, instance):
        return self._get_serializer_for_type(
            type_value=getattr(instance, self.resource_type_field_name)
        )

    def _get_serializer_for_data(self, data):
        try:
            return self._get_serializer_for_type(
                type_value=data[self.resource_type_field_name]
            )
        except KeyError:
            raise ValidationError(
                f"{self.resource_type_field_name} is a required field."
            )
