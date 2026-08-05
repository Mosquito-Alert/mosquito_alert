from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from mosquito_alert.geo.models import TemporaryBoundary


class TemporaryBoundarySerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    expires_in = serializers.IntegerField(
        read_only=True, help_text="Time in seconds until this cached boundary expires."
    )
    geojson = GeometryField(write_only=True)

    def create(self, validated_data):
        try:
            boundary = TemporaryBoundary(geometry=validated_data["geojson"])
        except ValueError:
            raise serializers.ValidationError("Invalid geometry")

        boundary.save()
        return {"uuid": boundary.uuid, "expires_in": boundary.expires_in}
