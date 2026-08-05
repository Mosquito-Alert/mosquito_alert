from rest_framework import serializers

from mosquito_alert.api.v1.fields import TimezoneAwareDateTimeField
from mosquito_alert.fixes.models import Fix
from mosquito_alert.users.models import TigaUser


class FixLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fix
        fields = ("latitude", "longitude")
        extra_kwargs = {
            "latitude": {"source": "masked_lat"},
            "longitude": {"source": "masked_lon"},
        }


class FixSerializer(serializers.ModelSerializer):
    created_at = TimezoneAwareDateTimeField(required=True, source="fix_time")
    sent_at = TimezoneAwareDateTimeField(required=True, source="phone_upload_time")

    coverage_uuid = serializers.UUIDField(source="user_coverage_uuid")
    point = FixLocationSerializer(source="*", required=True)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        request = self.context.get("request")
        user = request.user
        if request and user and user.is_authenticated:
            if isinstance(user, TigaUser):
                if (
                    user.last_location_update is None
                    or instance.fix_time >= user.last_location_update
                ):
                    user.last_location = instance.point
                    user.last_location_update = instance.fix_time
                    user.save()

        return instance

    class Meta:
        model = Fix
        fields = (
            "coverage_uuid",
            "created_at",
            "sent_at",
            "received_at",
            "point",
            "power",
        )
        read_only_fields = ("received_at",)
        extra_kwargs = {
            "received_at": {"source": "server_upload_time"},
        }
