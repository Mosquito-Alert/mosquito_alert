from django.db import models, transaction
from rest_framework import serializers

from mosquito_alert.devices.models import Device, MobileApp
from mosquito_alert.reports.models import Report


class DeviceSerializer(serializers.ModelSerializer):
    class MobileAppSerializer(serializers.ModelSerializer):
        class Meta:
            model = MobileApp
            fields = ("package_name", "package_version")
            validators = []  # disable auto UniqueTogetherValidator (will manage get_or_create in the parent serializer)

    class DeviceOsSerializer(serializers.ModelSerializer):
        class Meta:
            model = Device
            fields = (
                "name",
                "version",
                "locale",
            )
            extra_kwargs = {
                "name": {"source": "os_name", "required": True, "allow_null": False},
                "version": {
                    "source": "os_version",
                    "required": True,
                    "allow_null": False,
                },
                "locale": {"source": "os_locale"},
            }

    mobile_app = MobileAppSerializer(required=False)
    os = DeviceOsSerializer(source="*")
    user_uuid = serializers.UUIDField(
        source="user_id", allow_null=False, read_only=True
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    @transaction.atomic
    def create(self, validated_data):
        # Extract the user and model from the data
        user = validated_data.get("user")
        model = validated_data.get("model")
        device_id = validated_data.get("device_id")

        # Extract mobile app data.
        mobile_app_data = validated_data.pop("mobile_app", None)
        if mobile_app_data:
            validated_data["mobile_app"], _ = MobileApp.objects.get_or_create(
                **mobile_app_data
            )

        # Check if there is a device with the same user, model, and device_id=None
        # That is for the users that are migrating from the legacy API to this.
        devices_to_deduplicate_qs = Device.objects.filter(
            models.Q(model=model)
            | models.Q(registration_id=validated_data.get("registration_id"))
        ).filter(user=user, device_id=None)

        if device := devices_to_deduplicate_qs.order_by("date_created").first():
            devices_to_delete = devices_to_deduplicate_qs.exclude(
                pk=device.pk
            ) | Device.objects.filter(user=user, model=model, device_id=device_id)
            Report.objects.filter(device__in=devices_to_delete).update(device=device)
            devices_to_delete.delete()
            # If device exists, update it
            for attr, value in validated_data.items():
                setattr(device, attr, value)
            device.save()
            return device

        # If no matching device was found, create a new device
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        # Extract mobile app data.
        mobile_app_data = validated_data.pop("mobile_app", None)
        if mobile_app_data:
            validated_data["mobile_app"], _ = MobileApp.objects.get_or_create(
                **mobile_app_data
            )

        return super().update(instance, validated_data)

    class Meta:
        model = Device
        fields = (
            "device_id",
            "name",
            "fcm_token",
            "type",
            "manufacturer",
            "model",
            "os",
            "mobile_app",
            "user_uuid",
            "last_login",
            "user",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
            "last_login",
        )
        extra_kwargs = {
            "device_id": {
                "required": True,
                "allow_null": False,
                "allow_blank": False,
                "default": serializers.empty,
            },
            "fcm_token": {
                "source": "registration_id",
                "write_only": True,
                "required": True,
                "allow_null": False,
            },
            "created_at": {"source": "date_created", "allow_null": False},
            "type": {"required": True, "allow_null": False},
            "model": {"required": True, "allow_null": False},
            "last_login": {"allow_null": True},
        }


class DeviceUpdateSerializer(DeviceSerializer):
    class Meta(DeviceSerializer.Meta):
        read_only_fields = DeviceSerializer.Meta.read_only_fields + (
            "device_id",
            "type",
            "manufacturer",
            "model",
        )
        extra_kwargs = {
            **DeviceSerializer.Meta.extra_kwargs,
            "manufacturer": {"allow_null": True},
        }
