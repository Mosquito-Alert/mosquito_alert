from drf_spectacular.contrib.rest_polymorphic import PolymorphicSerializerExtension
from drf_spectacular.drainage import warn
from drf_spectacular.extensions import (
    OpenApiSerializerFieldExtension,
)
from drf_spectacular.plumbing import build_object_type, build_basic_type
from drf_spectacular.types import OpenApiTypes


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

class FieldPolymorphicSerializerExtension(PolymorphicSerializerExtension):
    target_class = "api.base_serializers.FieldPolymorphicSerializer"

    # NOTE: even if the implementation in PolymorphicSerializerExtension works pretty well,
    # it causes errors on openapi-generator.
    # That is because it's creating a Typed component (see self.build_typed_component())
    # And it's a bug in the generator: https://github.com/OpenAPITools/openapi-generator/issues/19261
    # See: https://redocly.com/docs/resources/discriminator
    def map_serializer(self, auto_schema, direction):
        sub_components = []
        serializer = self.target

        for (
            resource_type_field_name_value,
            sub_serializer,
        ) in self.target.field_value_serializer_mapping.items():
            sub_serializer.partial = serializer.partial
            component = auto_schema.resolve_serializer(sub_serializer, direction)

            # Define the discriminator field schema
            field_schema = build_basic_type(OpenApiTypes.STR)
            field_schema['enum'] = [resource_type_field_name_value,] # NOTE: in openapi 3.1 is 'const'
            # field_schema['default'] = resource_type_field_name_value

            component.schema['properties'] = {
                serializer.resource_type_field_name: field_schema,
                **component.schema['properties']
            }
            component.schema['required'].append(serializer.resource_type_field_name)

            sub_components.append((resource_type_field_name_value, component.ref))

            if not resource_type_field_name_value:
                warn(
                    f'discriminator mapping key is empty for {sub_serializer.__class__}. '
                    f'this might lead to code generation issues.'
                )

        one_of_list = []
        for _, ref in sub_components:
            if ref not in one_of_list:
                one_of_list.append(ref)

        return {
            "oneOf": one_of_list,
            "discriminator": {
                "propertyName": serializer.resource_type_field_name,
                "mapping": {
                    resource_type_field_name_value: ref["$ref"]
                    for resource_type_field_name_value, ref in sub_components},
            }
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
