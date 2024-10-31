from drf_spectacular.extensions import (
    OpenApiSerializerFieldExtension,
    OpenApiSerializerExtension,
)
from drf_spectacular.plumbing import build_object_type, build_basic_type
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.plumbing import force_instance


class PointFieldExtension(OpenApiSerializerFieldExtension):
    target_class = "drf_extra_fields.geo_fields.PointField"

    def map_serializer_field(self, auto_schema, direction):
        openapi_type = OpenApiTypes.STR if self.target.str_points else OpenApiTypes.FLOAT
        return build_object_type(
            properties={
                "latitude": build_basic_type(openapi_type),
                "longitude": build_basic_type(openapi_type),
            },
            required=["latitude", "longitude"] if self.target.required else None
        )

class FieldPolymorphicSerializerExtension(OpenApiSerializerExtension):
    target_class = "api.base_serializers.FieldPolymorphicSerializer"

    def get_name(self):
        return self.target.model._meta.model_name

    def map_serializer(self, auto_schema, direction):
        sub_components = []
        for (
            resource_type_field_name,
            sub_serializer,
        ) in self.target.field_value_serializer_mapping.items():
            sub_serializer = force_instance(sub_serializer)
            resolved = auto_schema.resolve_serializer(sub_serializer, direction)
            sub_components.append((resource_type_field_name, resolved.ref))

        return {
            "oneOf": [schema for _, schema in sub_components],
            "discriminator": {
                "propertyName": self.target.resource_type_field_name,
                "mapping": {
                    resource_type: schema["$ref"]
                    for resource_type, schema in sub_components
                },
            },
        }


class ReportSerializerExtension(FieldPolymorphicSerializerExtension):
    target_class = "api.serializers.ReportSerializer"


class WritableSerializerMethodField(OpenApiSerializerFieldExtension):
    target_class = "api.fields.WritableSerializerMethodField"

    def map_serializer_field(self, auto_schema, direction):
        return auto_schema._map_serializer_field(
            field=self.target.deserializer_field if direction == 'request' else self.target.serializer_field,
            direction=direction,
            bypass_extensions=True
        )
