from django.db.models import Model
from django.core.exceptions import ImproperlyConfigured

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from tigaserver_app.models import TigaUser

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
        ret[self.resource_type_field_name] = getattr(instance, self.resource_type_field_name)
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
        validated_data[self.resource_type_field_name] = data[self.resource_type_field_name]
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

class LocalizedSerializerMixin:
    """
    A custom serializer field that supports localization for a dynamic field name.
    Allows calling with arguments such as 'title', 'message', max_length, help_text, etc.
    """
    def __init__(self, *args, **kwargs):
        # From CharField
        allow_blank = kwargs.pop('allow_blank', False)
        trim_whitespace = kwargs.pop('trim_whitespace', True)
        max_length = kwargs.pop('max_length', None)
        min_length = kwargs.pop('min_length', None)

        is_html = kwargs.pop('is_html', False)

        super().__init__(*args, **kwargs)

        required_languages = kwargs.get('required_languages', ['en'])

        # Sort the languages alphabetically based on the language code
        for code, name in sorted(TigaUser.AVAILABLE_LANGUAGES, key=lambda x: x[0]):
            # Use max_length if provided and if the field is for 'title'
            field_params = {
                'required': code in required_languages,
                'allow_blank': allow_blank,
                'trim_whitespace': trim_whitespace,
                'max_length': max_length,
                'min_length': min_length,
                'help_text': name
            }
            field_klass = HTMLCharField if is_html else serializers.CharField
            self.fields[code] = field_klass(**field_params)
