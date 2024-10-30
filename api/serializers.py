from datetime import datetime
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from drf_extra_fields.geo_fields import PointField
from taggit.serializers import TaggitSerializer

from tigacrafting.models import ExpertReportAnnotation
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
    MobileApp,
    IAScore
)

from .fields import (
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    IntegerDefaultField,
    TagListSerializerField,
    TimeZoneSerializerChoiceField,
    LocalizedField
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
    class NotificationMessageSerializer(serializers.ModelSerializer):
        # Localized results
        title = serializers.SerializerMethodField()
        body = serializers.SerializerMethodField()

        def get_title(self, obj) -> str:
            if obj.notification_content is None:
                return ""

            language_code = None
            user = self.context.get("request").user
            if user and isinstance(user, TigaUser):
                language_code = user.locale

            return obj.notification_content.get_title(
                language_code=language_code
            )

        def get_body(self, obj) -> str:
            if obj.notification_content is None:
                return ""

            language_code = None
            user = self.context.get("request").user
            if user and isinstance(user, TigaUser):
                language_code = user.locale

            return obj.notification_content.get_body(
                language_code=language_code
            )
        class Meta:
            model = Notification
            fields = ("title", "body")

    message = NotificationMessageSerializer(source='*', read_only=True)
    is_read = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        required=True
    )

    def get_is_read(self, obj) -> bool:
        user = self.context.get("request").user
        if not isinstance(user, TigaUser):
            return False

        if not hasattr(obj, 'notification_acknowledgements'):
            return False

        return obj.notification_acknowledgements.filter(
            user=self.context.get("request").user
        ).exists() or (obj.user == user and obj.acknowledged)


    def update(self, instance, validated_data):
        is_read = validated_data.pop("is_read", None)
        instance = super().update(instance, validated_data)

        if is_read is not None:
            if is_read is True:
                instance.mark_as_seen_for_user(user=self.context.get("request").user)
            else:
                instance.mark_as_unseen_for_user(user=self.context.get("request").user)

        return instance

    class Meta:
        model = Notification
        fields = (
            "id",
            "message",
            "is_read",
            "created_at"
        )
        read_only_fields = (
            "created_at",
        )
        extra_kwargs = {
            "created_at": {"source": "date_comment"}
        }

class CreateNotificationSerializer(serializers.ModelSerializer):
    class CreateNotificationMessageSerializer(serializers.Serializer):
        title = LocalizedField(
            max_length=255,
            help_text="Provide the message's title in all supported languages"
        )
        body = LocalizedField(
            help_text="Provide the message's body in all supported languages"
        )
        class Meta:
            fields = ("title", "body")

    created_at = serializers.DateTimeField(source="date_comment", read_only=True)
    expert = serializers.HiddenField(default=serializers.CurrentUserDefault())
    message = CreateNotificationMessageSerializer(
        many=False,
        write_only=True,
        help_text='The message of the notification'
    )
    receiver_type = serializers.ChoiceField(
        choices=["user", "topic"],
        write_only=True,
        required=True
    )

    @transaction.atomic
    def create(self, validated_data, user: Optional[TigaUser] = None):
        # Pop receiver_type since is not used on any model
        del validated_data["receiver_type"]

        message = validated_data.pop('message')
        titles = message.pop('title')
        bodies = message.pop('body')

        validated_data["notification_content"] = NotificationContent.objects.create(
            title_en=titles.get("en"),
            body_html_en=bodies.get("en"),
            title_es=titles.get("es"),
            body_html_es=bodies.get("en"),
            title_ca=titles.get("ca"),
            body_html_ca=bodies.get("ca"),
            title_native=titles.get(user.locale) if user else None,
            body_html_native=bodies.get(user.locale) if user else None,
            native_locale=user.locale if user else None,
        )

        return super().create(validated_data=validated_data)

    class Meta:
        model = Notification
        fields = (
            "receiver_type",
            "id",
            "message",
            "created_at",
            "expert"
        )

class UserNotificationCreateSerializer(CreateNotificationSerializer):
    user_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1,
        write_only=True
    )

    def validate(self, data):
        user_uuids = data.pop('user_uuids')
        users = TigaUser.objects.filter(pk__in=user_uuids)
        if users.count() != len(user_uuids):
            raise serializers.ValidationError("Some users were not found.")
        data["users"] = users
        return data

    def create(self, validated_data):
        result = []
        for user in validated_data.pop('users'):
            instance = super().create(validated_data, user=user)
            instance.send_to_user(user=user)
            result.append(instance)

        return result

    class Meta(CreateNotificationSerializer.Meta):
        fields = CreateNotificationSerializer.Meta.fields + (
            "user_uuids",
        )


class TopicNotificationCreateSerializer(CreateNotificationSerializer):
    topic_codes = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=1,
        write_only=True
    )

    def validate(self, data):
        topic_codes = data.pop('topic_codes')
        topics = NotificationTopic.objects.filter(topic_code__in=topic_codes)
        if topics.count() != len(topic_codes):
            raise serializers.ValidationError("Some topics were not found.")
        data["topics"] = topics
        return data

    def create(self, validated_data):
        topics = validated_data.pop('topics')

        result = []
        instance = super().create(validated_data)
        result.append(instance)

        for topic in topics:
            instance.send_to_topic(topic=topic)

        return result

    class Meta(CreateNotificationSerializer.Meta):
        fields = CreateNotificationSerializer.Meta.fields + ("topic_codes", )

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
    language_iso = serializers.SerializerMethodField(help_text='ISO 639-1 code')
    username = serializers.SerializerMethodField()
    is_guest = serializers.SerializerMethodField()

    def get_is_guest(self, obj) -> bool:
        return True

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_language_iso(self, obj) -> str:
        return obj.language_iso2

    class Meta:
        model = TigaUser
        fields = (
            "uuid",
            "username",
            "registration_time",
            "locale",
            "language_iso",
            "is_guest",
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
class PredictionSerializer(serializers.ModelSerializer):

    class_name_to_category = {
        'ae_aegypti': 5,
        'ae_albopictus': 4,
        'anopheles': 2,
        'culex': 10,
        'culiseta': 2,
        'ae_japonicus': 6,
        'ae_koreicus': 7,
        'other_species': 2,
        'not_sure': 9,
    }

    class_name_to_otherspecies = {
        'anopheles': 101,
        'culiseta': 103
    }

    class BoundingBoxSerializer(serializers.ModelSerializer):
        class Meta:
            model = IAScore
            fields = (
                'x_min',
                'y_min',
                'x_max',
                'y_max',
            )
            extra_kwargs = {
                "x_min": {"source": "x_tl"},
                "y_min": {"source": "y_tl"},
                "x_max": {"source": "x_br"},
                "y_max": {"source": "y_br"},
            }

    class PredictionScoreSerializer(serializers.ModelSerializer):
        class Meta:
            model = IAScore
            fields = IAScore.CLASS_FIELDNAMES

    id = serializers.IntegerField(source="pk", read_only=True, help_text="Unique identifier for the prediction.")
    bbox = BoundingBoxSerializer(source='*')
    scores = PredictionScoreSerializer(source='*')
    class_name = serializers.SerializerMethodField()
    class_score = serializers.SerializerMethodField()
    is_executive_validation = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        default=False,
    )

    def get_class_name(self, obj) -> str:
        return obj.class_name

    def get_class_score(self, obj) -> float:
        return obj.class_score

    def get_is_executive_validation(self, obj) -> bool:
        return not obj.expert_annotation is None

    def create(self, validated_data):
        is_executive_validation = validated_data.pop('is_executive_validation')

        validated_data['report'] = validated_data['photo'].report

        instance = super().create(validated_data)

        if is_executive_validation:
            obj = ExpertReportAnnotation.objects.create(
                user=get_user_model().objects.get(username='aima'),
                report=instance.photo.report,
                best_photo=instance.photo,
                category_id=self.class_name_to_category.get(self.get_class_name(obj=instance)),
                validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY,
                validation_complete=True,
                validation_complete_executive=True,
                simplified_annotation=False,
                status=1,  # Force public
                # edited_user_notes="", # TODO: value for publication,
                other_species=self.class_name_to_otherspecies.get(self.get_class_name(obj=instance))
            )
            instance.expert_annotation = obj
            instance.save()

        return instance

    class Meta:
        model = IAScore
        fields = (
            'id',
            'bbox',
            'insect_confidence',
            'class_name',
            'class_score',
            'scores',
            'is_executive_validation'
        )