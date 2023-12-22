from abc import abstractmethod

from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

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
)
from .base_serializers import FieldPolymorphicSerializer
from .fields import (
    ExpandedPointField,
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    TimeZoneSerializerChoiceField,
    IntegerDefaultField,
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
        fields = ("id", "name_engl", "iso3_code")
        extra_kwargs = {
            "id": {"source": "gid"},
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
class DetailNotificationSerializer(serializers.ModelSerializer):
    report_uuid = serializers.UUIDField(
        source="report_id", required=False, read_only=True, allow_null=True
    )

    seen = WritableSerializerMethodField(
        deserializer_field=serializers.BooleanField(required=True)
    )

    # Localized results
    title = serializers.SerializerMethodField(read_only=True)
    body = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_seen(self, obj):
        user = self.context.get("request").user
        if not isinstance(user, TigaUser):
            return False

        if not hasattr(obj, 'notification_acknowledgements'):
            return False

        return obj.notification_acknowledgements.filter(
            user=self.context.get("request").user
        ).exists() or (obj.user == user and obj.acknowledged)

    def set_seen(self, value):
        return value

    @extend_schema_field(OpenApiTypes.STR)
    def get_title(self, obj):
        if obj.notification_content is None:
            return ""

        return obj.notification_content.get_title(
            language_code=self.context.get("request").LANGUAGE_CODE
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_body(self, obj):
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
            "report_uuid",
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


class BaseNotificationCreateSerializer(serializers.ModelSerializer):
    @property
    @abstractmethod
    def RECEIVER_TYPE(self):
        raise NotImplementedError

    receiver_type = WritableSerializerMethodField(
        deserializer_field=serializers.ChoiceField(
            choices=["user", "topic"], write_only=True
        ),
    )

    title_en = serializers.CharField(write_only=True)
    body_en = serializers.CharField(write_only=True)

    created_at = serializers.DateTimeField(source="date_comment", read_only=True)
    expert = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def set_receiver_type(self, value):
        return value

    @extend_schema_field(OpenApiTypes.STR)
    def get_receiver_type(self, obj):
        return self.RECEIVER_TYPE

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
        fields = ("id", "receiver_type", "created_at", "title_en", "body_en")


class UserNotificationCreateSerializer(BaseNotificationCreateSerializer):
    RECEIVER_TYPE = "user"

    report_uuid = serializers.UUIDField(
        source="report_id", write_only=True, required=False, allow_null=True
    )
    user_uuid = serializers.UUIDField(write_only=True)

    def create(self, validated_data):
        user_uuid = validated_data.pop("user_uuid")

        instance = super().create(validated_data)

        if user_uuid:
            instance.send_to_user(user=TigaUser.objects.get(pk=user_uuid))

        return instance

    def validate(self, data):
        report_uuid = data.get("report_uuid", None)
        if report_uuid is not None:
            # Checking that the user is the owner of the report.
            if Report.objects.get(pk=report_uuid).user_id != data.get("user_uuid"):
                raise serializers.ValidationError(
                    "Can only assign report_uuid if the user is the owner of that report."
                )
        return data

    class Meta(BaseNotificationCreateSerializer.Meta):
        fields = (
            "receiver_type",
            "report_uuid",
            "user_uuid",
        ) + BaseNotificationCreateSerializer.Meta.fields


class TopicNotificationCreateSerializer(BaseNotificationCreateSerializer):
    RECEIVER_TYPE = "topic"

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

    class Meta(BaseNotificationCreateSerializer.Meta):
        fields = (
            "receiver_type",
            "topic_code",
        ) + BaseNotificationCreateSerializer.Meta.fields

#### END NOTIFICATION SERIALIZERS ####

class PartnerSerializer(serializers.ModelSerializer):
    point = ExpandedPointField(srid=4326)

    class Meta:
        model = OrganizationPin
        fields = ("id", "point", "description", "url")
        extra_kwargs = {
            "description": {"source": "textual_description"},
            "url": {"source": "page_url"},
        }

#### START REPORT SERIALIZERS ####

class ReportPhotoSerializer(serializers.ModelSerializer):
    url = serializers.ImageField(
        source="photo", use_url=True, read_only=True,
        help_text="URL of the photo associated with the item. Note: This URL may change over time. Do not rely on it for permanent storage."
    )
    file = serializers.ImageField(source="photo", write_only=True)

    class Meta:
        model = Photo
        fields = ("id", "url", "file")


class BaseReportSerializer(serializers.ModelSerializer):
    class DeviceSerializer(serializers.ModelSerializer):
        class Meta:
            model = Report
            fields = ("manufacturer", "model", "os", "os_version", "os_language")
            extra_kwargs = {
                "manufacturer": {"source": "device_manufacturer"},
                "model": {"source": "device_model"},
            }

    class PackageSerializer(serializers.ModelSerializer):
        class Meta:
            model = Report
            fields = ("name", "version", "language")
            extra_kwargs = {
                "name": {"source": "package_name"},
                "version": {"source": "package_version"},
                "language": {"source": "app_language"},
            }

    class ReportLocationSerializer(serializers.ModelSerializer):
        point = ExpandedPointField(srid=4326, required=True, allow_null=True)

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
    sent_at = TimezoneAwareDateTimeField(required=True, source="phone_upload_time")
    timezone = TimeZoneSerializerChoiceField(
        use_pytz=True,
        required=True,
        write_only=True,
        source="phone_timezone",
        help_text=Report._meta.get_field("phone_timezone").help_text,
    )

    received_at = serializers.DateTimeField(read_only=True, source="server_upload_time")

    location = ReportLocationSerializer(source="*")
    package = PackageSerializer(required=False, write_only=True, source="*")
    device = DeviceSerializer(required=False, write_only=True, source="*")

    class Meta:
        model = Report
        fields = (
            "uuid",
            "short_id",
            "user_uuid",
            "user",
            "type",
            "session_id",
            "created_at",
            "sent_at",
            "timezone",
            "received_at",
            "updated_at",
            "location",
            "note",
            "package",
            "device",
            "published",
        )
        read_only_fields = (
            "user_uuid",
            "updated_at",
            "received_at",
        )


class BaseReportWithPhotosSerializer(BaseReportSerializer):
    photos = ReportPhotoSerializer(required=False, many=True)

    def create(self, validated_data):
        photos = validated_data.pop("photos", [])

        instance = super().create(validated_data)

        for photo in photos:
            _ = Photo.objects.create(report=instance, **photo)

        return instance

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + ("photos",)


class ReportSerializer(FieldPolymorphicSerializer):
    class AdultReportSerializer(BaseReportWithPhotosSerializer):
        class Meta(BaseReportWithPhotosSerializer.Meta):
            fields = BaseReportWithPhotosSerializer.Meta.fields + (
                "event_environment",
                "event_moment",
                "user_perceived_mosquito_specie",
                "user_perceived_mosquito_thorax",
                "user_perceived_mosquito_abdomen",
                "user_perceived_mosquito_legs",
            )

    class BiteReportSerializer(BaseReportSerializer):
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

    class BreedingSiteReportSerializer(BaseReportWithPhotosSerializer):
        class Meta(BaseReportWithPhotosSerializer.Meta):
            fields = BaseReportWithPhotosSerializer.Meta.fields + (
                "breeding_site_type",
                "breeding_site_has_water",
                "breeding_site_in_public_area",
                "breeding_site_has_near_mosquitoes",
                "breeding_site_has_larvae",
            )
            extra_kwargs = {
                "breeding_site_type": {"allow_null": False},
                # Need to set default to None, otherwise BooleanField uses False
                "breeding_site_has_water": {"allow_null": True, "default": None},
                "breeding_site_in_public_area": {"allow_null": True, "default": None},
                "breeding_site_has_near_mosquitoes": {
                    "allow_null": True,
                    "default": None,
                },
                "breeding_site_has_larvae": {"allow_null": True, "default": None},
            }

    class MissionReportSerializer(BaseReportSerializer):
        class Meta(BaseReportSerializer.Meta):
            fields = BaseReportSerializer.Meta.fields + ("mission_id",)

    field_value_serializer_mapping = {
        Report.TYPE_ADULT: AdultReportSerializer,
        Report.TYPE_BITE: BiteReportSerializer,
        Report.TYPE_SITE: BreedingSiteReportSerializer,
        Report.TYPE_MISSION: MissionReportSerializer,
    }
    resource_type_field_name = "type"
    model = Report

#### END REPORT SERIALIZERS ####


class UserSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField(source="user_UUID", read_only=True)

    class Meta:
        model = TigaUser
        fields = (
            "uuid",
            "registration_time",
            "device_token",
            "score",
            "last_score_update",
        )
        read_only_fields = (
            "registration_time",
            "score",
            "last_score_update",
        )
        extra_kwargs = {
            "device_token": {"write_only": True},
            "score": {"source": "score_v2"}
        }

