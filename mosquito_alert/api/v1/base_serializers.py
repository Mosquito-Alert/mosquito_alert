from django.db.models import Model
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language_info

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from modeltranslation.translator import translator

from .fields import HTMLCharField


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

        instance = super().__new__(cls, *args, **kwargs)

        field_value_serializer_mapping = cls.field_value_serializer_mapping
        instance.field_value_serializer_mapping = {}
        for field_value, serializer in field_value_serializer_mapping.items():
            if isinstance(serializer, serializers.Serializer):
                serializer = serializer
            else:
                serializer = serializer(*args, **kwargs)
                serializer.parent = instance

            instance.field_value_serializer_mapping[field_value] = serializer

        return instance

    def to_representation(self, instance):
        serializer = self._get_serializer_for_instance(instance=instance)
        ret = serializer.to_representation(instance)
        ret[self.resource_type_field_name] = getattr(
            instance, self.resource_type_field_name
        )
        return ret

    def to_internal_value(self, data):
        if self.instance:
            serializer = self._get_serializer_for_instance(instance=self.instance)
        else:
            serializer = self._get_serializer_for_data(data=data)
        ret = serializer.to_internal_value(data=data)
        ret[self.resource_type_field_name] = data[self.resource_type_field_name]
        return ret

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
        validated_data = serializer.run_validation(data)
        validated_data[self.resource_type_field_name] = data[
            self.resource_type_field_name
        ]
        return validated_data

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


class LocalizedModelSerializerMixin:
    """
    A custom serializer field that supports localization for a dynamic field name.
    Allows calling with arguments such as 'title', 'message', max_length, help_text, etc.
    """

    def __init__(self, *args, **kwargs):
        self.allow_blank = kwargs.pop("allow_blank", False)
        self.trim_whitespace = kwargs.pop("trim_whitespace", True)
        self.max_length = kwargs.pop("max_length", None)
        self.min_length = kwargs.pop("min_length", None)

        self.is_html = kwargs.pop("is_html", False)
        self.required_languages = kwargs.pop("required_languages", [])
        if source := kwargs.pop("source"):
            self.source_field = source.split(".")[-1]
            kwargs["source"] = source.split(".")[0]

        super().__init__(*args, **kwargs)

    def get_fields(self):
        trans_opts = translator.get_options_for_model(self.Meta.model)
        trans_field = trans_opts.fields.get(self.source_field)

        result = {}
        for field in sorted(trans_field, key=lambda x: x.language):
            field_params = {
                "source": field.name,
                "required": field.language in self.required_languages,
                "allow_blank": self.allow_blank,
                "allow_null": field.language not in self.required_languages,
                "trim_whitespace": self.trim_whitespace,
                "max_length": self.max_length,
                "min_length": self.min_length,
                "help_text": get_language_info(field.language)["name_local"].title(),
            }
            field_klass = HTMLCharField if self.is_html else serializers.CharField
            result[field.language] = field_klass(**field_params)
        return result
