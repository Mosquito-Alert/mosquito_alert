from abc import abstractmethod
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from rest_framework import serializers

from drf_extra_fields.geo_fields import PointField
from taggit.serializers import TaggitSerializer

from tigaserver_app.models import (
    NotificationContent,
    Notification,
    OrganizationPin,
    OWCampaigns,
    EuropeCountry,
    TigaUser,
    Report,
    Photo,
    Fix,
    NotificationTopic,
    Device,
    MobileApp
)

from .fields import (
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    IntegerDefaultField,
    TagListSerializerField,
    TimeZoneSerializerChoiceField
)

User = get_user_model()


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = OWCampaigns
        fields = ("id", "country_id", "posting_address", "start_date", "end_date")
        extra_kwargs = {
            "start_date": {"source": "campaign_start_date"},
            "end_date": {"source": "campaign_end_date"},
        }


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = EuropeCountry
        fields = ("id", "name_en", "iso3_code")
        extra_kwargs = {
            "id": {"source": "gid"},
            "name_en": {"source": "name_engl"}
        }


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


#### START NOTIFICATION SERIALIZERS ####
class NotificationSerializer(serializers.ModelSerializer):

    seen = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        required=True
    )

    # Localized results
    title = serializers.SerializerMethodField(read_only=True)
    body = serializers.SerializerMethodField(read_only=True)

    def get_seen(self, obj) -> bool:
        user = self.context.get("request").user
        if not isinstance(user, TigaUser):
            return False

        if not hasattr(obj, 'notification_acknowledgements'):
            return False

        return obj.notification_acknowledgements.filter(
            user=self.context.get("request").user
        ).exists() or (obj.user == user and obj.acknowledged)

    def get_title(self, obj) -> str:
        if obj.notification_content is None:
            return ""

        return obj.notification_content.get_title(
            language_code=self.context.get("request").LANGUAGE_CODE
        )

    def get_body(self, obj) -> str:
        if obj.notification_content is None:
            return ""

        return obj.notification_content.get_body(
            language_code=self.context.get("request").LANGUAGE_CODE
        )

    def update(self, instance, validated_data):
        seen = validated_data.pop("seen", None)
        instance = super().update(instance, validated_data)

        if seen is not None:
            if seen is True:
                instance.mark_as_seen_for_user(user=self.context.get("request").user)
            else:
                instance.mark_as_unseen_for_user(user=self.context.get("request").user)

        return instance

    class Meta:
        model = Notification
        fields = (
            "id",
            "expert_id",
            "created_at",
            "title",
            "body",
            "seen",
        )
        read_only_fields = (
            "created_at",
            "title",
            "body",
        )
        extra_kwargs = {
            "created_at": {"source": "date_comment"}
        }

class CreateNotificationSerializer(serializers.ModelSerializer):

    title_en = serializers.CharField(write_only=True)
    body_en = serializers.CharField(write_only=True)

    created_at = serializers.DateTimeField(source="date_comment", read_only=True)
    expert = serializers.HiddenField(default=serializers.CurrentUserDefault())

    receiver_type = serializers.ChoiceField(
            choices=["user", "topic"],
            write_only=True,
            required=True
        )

    @transaction.atomic
    def create(self, validated_data):
        # Pop receiver_type since is not used on any model
        del validated_data["receiver_type"]

        validated_data["notification_content"] = NotificationContent.objects.create(
            title_en=validated_data.pop("title_en"),
            body_html_en=validated_data.pop("body_en"),
        )

        return super().create(validated_data=validated_data)

    class Meta:
        model = Notification
        fields = (
            "receiver_type",
            "id",
            "created_at",
            "title_en",
            "body_en",
            "expert"
        )

class UserNotificationCreateSerializer(CreateNotificationSerializer):
    user_uuid = serializers.UUIDField(write_only=True)

    def create(self, validated_data):
        user_uuid = validated_data.pop("user_uuid")

        instance = super().create(validated_data)

        if user_uuid:
            instance.send_to_user(user=TigaUser.objects.get(pk=user_uuid))

        return instance

    class Meta(CreateNotificationSerializer.Meta):
        fields = CreateNotificationSerializer.Meta.fields + (
            "user_uuid",
        )


class TopicNotificationCreateSerializer(CreateNotificationSerializer):
    topic_code = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        topic_code = data.pop("topic_code")
        try:
            data["topic"] = NotificationTopic.objects.get(topic_code=topic_code)
        except NotificationTopic.DoesNotExist:
            raise serializers.ValidationError("topic_code is not valid.")

        return data

    @transaction.atomic
    def create(self, validated_data):
        topic = validated_data.pop("topic")

        instance = super().create(validated_data)

        if topic:
            instance.send_to_topic(topic=topic)

        return instance

    class Meta(CreateNotificationSerializer.Meta):
        fields = CreateNotificationSerializer.Meta.fields + ("topic_code", )

#### END NOTIFICATION SERIALIZERS ####

class PartnerSerializer(serializers.ModelSerializer):
    point = PointField()

    class Meta:
        model = OrganizationPin
        fields = ("id", "point", "description", "url")
        extra_kwargs = {
            "description": {"source": "textual_description"},
            "url": {"source": "page_url"},
        }

#### START REPORT SERIALIZERS ####

class SimplePhotoSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(
        source="photo", use_url=True, read_only=True,
        help_text="URL of the photo associated with the item. Note: This URL may change over time. Do not rely on it for permanent storage."
    )
    file = serializers.ImageField(required=True, source="photo", write_only=True)

    class Meta:
        model = Photo
        fields = ("uuid", "url", "file")
        read_only_fields = (
            "uuid",
        )


class BaseReportSerializer(TaggitSerializer, serializers.ModelSerializer):

    class LocationSerializer(serializers.ModelSerializer):
        point = PointField(required=True, allow_null=True)
        timezone = TimeZoneSerializerChoiceField(read_only=True, allow_null=True)

        def to_internal_value(self, data):
            ret = super().to_internal_value(data)

            preffix = "current"
            if ret["location_choice"] == Report.LOCATION_SELECTED:
                preffix = "selected"

            point = ret.pop("point")
            ret[f"{preffix}_location_lat"] = point.y
            ret[f"{preffix}_location_lon"] = point.x

            return ret

        class Meta:
            model = Report
            fields = (
                "type",
                "point",
                "timezone",
                "country_id",
                "nuts_2",
                "nuts_3",
            )
            read_only_fields = (
                "country_id",
                "nuts_2",
                "nuts_3",
            )
            extra_kwargs = {
                "type": {"source": "location_choice"},
                "nuts_2": {"allow_null": True},
                "nuts_3": {"allow_null": True},
            }

    uuid = serializers.UUIDField(
        source="version_UUID", allow_null=False, read_only=True
    )
    short_id = serializers.CharField(
        source="report_id", allow_null=False, read_only=True
    )
    user_uuid = serializers.UUIDField(
        source="user_id", allow_null=False, read_only=True
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    created_at = TimezoneAwareDateTimeField(required=True, source="creation_time")
    created_at_local = serializers.SerializerMethodField(
        help_text="The date and time when the record was created, displayed in the local timezone specified for this entry."
    )
    sent_at = TimezoneAwareDateTimeField(required=True, source="phone_upload_time")

    received_at = serializers.DateTimeField(read_only=True, source="server_upload_time")

    location = LocationSerializer(source="*")
    tags = TagListSerializerField(required=False, allow_empty=True)

    def get_created_at_local(self, obj) -> datetime:
        return obj.creation_time_local

    class Meta:
        model = Report
        fields = (
            "uuid",
            "short_id",
            "user_uuid",
            "user",
            "created_at",
            "created_at_local",
            "sent_at",
            "received_at",
            "updated_at",
            "location",
            "note",
            "tags",
            "published",
        )
        read_only_fields = (
            "user_uuid",
            "updated_at",
            "received_at",
        )

class BaseReportWithPhotosSerializer(BaseReportSerializer):
    photos = SimplePhotoSerializer(required=True, many=True)

    def create(self, validated_data):
        photos = validated_data.pop("photos", [])

        instance = super().create(validated_data)

        for photo in photos:
            _ = Photo.objects.create(report=instance, **photo)

        return instance

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + ("photos",)

class ObservationSerializer(BaseReportWithPhotosSerializer):

    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_ADULT
        return super().create(validated_data)

    class Meta(BaseReportWithPhotosSerializer.Meta):
        fields = BaseReportWithPhotosSerializer.Meta.fields + (
            "event_environment",
            "event_moment",
            "user_perceived_mosquito_specie",
            "user_perceived_mosquito_thorax",
            "user_perceived_mosquito_abdomen",
            "user_perceived_mosquito_legs",
        )

class BiteSerializer(BaseReportSerializer):
    head_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("head_bite_count").help_text,
    )
    left_arm_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("left_arm_bite_count").help_text,
    )
    right_arm_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("right_arm_bite_count").help_text,
    )
    chest_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("chest_bite_count").help_text,
    )
    left_leg_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("left_leg_bite_count").help_text,
    )
    right_leg_bite_count = IntegerDefaultField(
        default=0,
        allow_null=True,
        help_text=Report._meta.get_field("right_leg_bite_count").help_text,
    )

    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_BITE
        return super().create(validated_data)

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + (
            "event_environment",
            "event_moment",
            "bite_count",
            "head_bite_count",
            "left_arm_bite_count",
            "right_arm_bite_count",
            "chest_bite_count",
            "left_leg_bite_count",
            "right_leg_bite_count",
        )
        read_only_fields = BaseReportSerializer.Meta.read_only_fields + (
            "bite_count",
        )

class BreedingSiteSerializer(BaseReportWithPhotosSerializer):
    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_SITE
        return super().create(validated_data)

    class Meta(BaseReportWithPhotosSerializer.Meta):
        fields = BaseReportWithPhotosSerializer.Meta.fields + (
            "site_type",
            "has_water",
            "in_public_area",
            "has_near_mosquitoes",
            "has_larvae",
        )
        extra_kwargs = {
            "site_type": {"allow_null": False, "source": "breeding_site_type"},
            # Need to set default to None, otherwise BooleanField uses False
            "has_water": {"allow_null": True, "default": None, "source": "breeding_site_has_water"},
            "in_public_area": {"allow_null": True, "default": None, "source": "breeding_site_in_public_area"},
            "has_near_mosquitoes": {
                "allow_null": True,
                "default": None,
                "source": "breeding_site_has_near_mosquitoes"
            },
            "has_larvae": {"allow_null": True, "default": None, "source": "breeding_site_has_larvae"},
        }

#### END REPORT SERIALIZERS ####


class UserSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="user_UUID", read_only=True)

    class Meta:
        model = TigaUser
        fields = (
            "uuid",
            "registration_time",
            "locale",
            "score",
            "last_score_update",
        )
        read_only_fields = (
            "registration_time",
            "score",
            "last_score_update",
        )
        extra_kwargs = {
            "score": {"source": "score_v2"}
        }

class CreateUserSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        instance = super().create(validated_data)
        instance.set_password(raw_password)
        instance.save()
        return instance
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("password",)

class PhotoSerializer(serializers.ModelSerializer):

    image_path = serializers.SerializerMethodField(help_text="Internal server path of the image.")

    def get_image_path(self, obj) -> str:
        return obj.photo.path

    class Meta:
        model = Photo
        fields = (
            "uuid",
            "image_url",
            "image_path"
        )
        extra_kwargs = {
            "image_url": {"source": "photo"},
        }

class MobileAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileApp
        fields = ("package_name", "package_version")

class DeviceSerializer(serializers.ModelSerializer):
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
                "version": {"source": "os_version", "required": True, "allow_null": False},
                "locale": {"source": "os_locale" }
            }

    mobile_app = MobileAppSerializer(required=False)
    os = DeviceOsSerializer(source="*")
    user_uuid = serializers.UUIDField(
        source="user_id", allow_null=False, read_only=True
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, data):
        mobile_app_data = data.pop("mobile_app", None)
        # Create or retrieve the MobileApp instance
        mobile_app_instance = None
        if mobile_app_data:
            mobile_app_instance, _ = MobileApp.objects.get_or_create(**mobile_app_data)
        data["mobile_app"] = mobile_app_instance

        return data

    def create(self, validated_data):
        # Extract the user and model from the data
        user = validated_data.get('user')
        model = validated_data.get('model')
        device_id = validated_data.get('device_id')

        # Check if there is a device with the same user, model, and device_id=None
        # That is for the users that are migrating from the legacy API to this.
        device = Device.objects.filter(user=user, model=model, device_id=None).first()
        if device:
            Device.objects.filter(user=user, model=model, device_id=device_id).delete()
            # If device exists, update it
            for attr, value in validated_data.items():
                setattr(device, attr, value)
            device.save()
            return device

        # If no matching device was found, create a new device
        return super().create(validated_data)

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
            "device_id": {"required": True, "allow_null": False },
            "fcm_token": {"source": "registration_id", "write_only": True, "required": True, "allow_null": False },
            "created_at": {"source": "date_created" },
            "type": {"required": True, "allow_null": False },
            "model": {"required": True, "allow_null": False },
            "last_login": { "allow_null": True },
        }

class DeviceUpdateSerializer(DeviceSerializer):
    class Meta(DeviceSerializer.Meta):
        read_only_fields = DeviceSerializer.Meta.read_only_fields + (
            "device_id",
            "type",
            "manufacturer",
            "model"
        )