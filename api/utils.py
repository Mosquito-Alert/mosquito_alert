from typing import List

from rest_framework import serializers

def get_fk_fieldnames(model, related_model) -> List:
    user_fk_fieldnames = []
    for field in model._meta.get_fields():
        if field.is_relation and field.related_model == related_model:
            user_fk_fieldnames.append(field.name)
    return user_fk_fieldnames

def get_serializer_field_paths_for_csv(serializer: serializers.BaseSerializer, separator: str, prefix: str ="") -> List[str]:
    fields = []

    # Unwrap ListSerializer (many=True)
    if isinstance(serializer, serializers.ListSerializer):
        serializer = serializer.child

    for name, field in serializer.fields.items():
        # Skip hidden or write-only fields
        if field.write_only:
            continue

        path = f"{prefix}{separator}{name}" if prefix else name

        # Skip list fields entirely
        if isinstance(field, (serializers.ListSerializer, serializers.ListField)):
            continue
        # Nested serializer
        if isinstance(field, serializers.BaseSerializer):
            fields.extend(get_serializer_field_paths_for_csv(field, separator, prefix=path))
        else:
            fields.append(path)

    return fields