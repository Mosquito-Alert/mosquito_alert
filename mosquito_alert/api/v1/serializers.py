from abc import abstractmethod
from datetime import datetime
from typing import Literal, Optional, Union
from uuid import UUID

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db import transaction, models
from django.utils import timezone

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.helpers import lazy_serializer

from rest_framework import serializers

from drf_extra_fields.geo_fields import PointField
import minify_html
from rest_framework_csv.renderers import CSVStreamingRenderer
from rest_framework_dataclasses.serializers import DataclassSerializer
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from taggit.serializers import TaggitSerializer, TagListSerializerField

from mosquito_alert.campaigns.models import OWCampaigns
from mosquito_alert.devices.models import Device, MobileApp
from mosquito_alert.fixes.models import Fix
from mosquito_alert.geo.models import (
    EuropeCountry,
    LauEurope,
    NutsEurope,
    TemporaryBoundary,
)
from mosquito_alert.identification_tasks.models import (
    IdentificationTask,
    ExpertReportAnnotation,
    PhotoPrediction,
)
from mosquito_alert.notifications.models import (
    Notification,
    NotificationContent,
    NotificationTopic,
    NotificationRecipient,
)
from mosquito_alert.partners.models import OrganizationPin
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.users.models import UserStat, TigaUser
from mosquito_alert.users.permissions import Permissions, Role

from .base_serializers import LocalizedModelSerializerMixin
from .fields import (
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    IntegerDefaultField,
    TimeZoneSerializerChoiceField,
    HTMLCharField,
)
from .mixins import ReportGeoJsonModelSerializerMixin

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
        extra_kwargs = {"id": {"source": "gid"}, "name_en": {"source": "name_engl"}}


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


class PermissionsSerializer(DataclassSerializer):
    class Meta:
        dataclass = Permissions


class BaseRolePermissionSerializer(serializers.Serializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    @abstractmethod
    def _get_role(self, obj: Union[User, TigaUser]) -> Role:
        raise NotImplementedError

    def get_role(self, obj: Union[User, TigaUser]) -> Role:
        if isinstance(obj, User):
            try:
                obj = obj.userstat
            except UserStat.DoesNotExist:
                obj = None

        if not obj:
            obj = TigaUser()
        return self._get_role(obj=obj)

    @extend_schema_field(PermissionsSerializer)
    def get_permissions(self, obj: Union[User, TigaUser]):
        if isinstance(obj, User):
            try:
                obj = obj.userstat
            except UserStat.DoesNotExist:
                obj = None

        if not obj:
            obj = TigaUser()

        permissions = obj.get_role_permissions(role=self.get_role(obj=obj))
        return PermissionsSerializer(permissions).data


class UserPermissionSerializer(serializers.Serializer):
    class GeneralPermissionSerializer(BaseRolePermissionSerializer):
        is_staff = serializers.BooleanField()

        def _get_role(self, obj: Union[User, TigaUser]) -> Role:
            return obj.get_role()

    class CountryPermissionSerializer(BaseRolePermissionSerializer):
        def __init__(self, *args, **kwargs):
            self.country = kwargs.pop("country", None)
            super().__init__(*args, **kwargs)

        country = serializers.SerializerMethodField()

        def _get_role(self, obj: Union[User, TigaUser]) -> Role:
            return obj.get_role(country=self.country)

        @extend_schema_field(CountrySerializer)
        def get_country(self, obj: Union[User, TigaUser]):
            return CountrySerializer(self.country).data

    general = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()

    @extend_schema_field(GeneralPermissionSerializer)
    def get_general(self, obj: Union[User, TigaUser]):
        return self.GeneralPermissionSerializer(obj).data

    @extend_schema_field(CountryPermissionSerializer(many=True))
    def get_countries(self, obj: Union[User, TigaUser]):
        if isinstance(obj, User):
            try:
                obj = obj.userstat
            except UserStat.DoesNotExist:
                obj = None
        if not obj:
            return self.CountryPermissionSerializer(many=True).data

        result = []
        for country in obj.get_countries_with_roles():
            result.append(
                self.CountryPermissionSerializer(instance=obj, country=country).data
            )
        return result


class UserSerializer(serializers.ModelSerializer):
    class UserScoreSerializer(serializers.ModelSerializer):
        value = serializers.IntegerField(source="score_v2", min_value=0, read_only=True)
        updated_at = serializers.DateTimeField(
            source="last_score_update", read_only=True, allow_null=True
        )

        class Meta:
            model = TigaUser
            fields = ("value", "updated_at")

    uuid = serializers.UUIDField(source="user_UUID", read_only=True)
    language_iso = serializers.SerializerMethodField(
        help_text="ISO 639-1 code", default="en"
    )
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_guest = serializers.SerializerMethodField()
    score = UserScoreSerializer(source="*", read_only=True)

    def get_is_guest(self, obj) -> bool:
        return True

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_first_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.first_name
        return "Anonymous"

    def get_last_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.last_name
        return "User"

    def get_full_name(self, obj) -> str:
        if isinstance(obj, User):
            return obj.get_full_name()
        return "Anonymous User"

    def get_language_iso(self, obj) -> str:
        return obj.language_iso2

    def to_representation(self, instance):
        if isinstance(instance, User):
            # NOTE: this must be the same structure as defined.
            data = {}
            data["uuid"] = UUID(int=instance.pk)
            data["username"] = instance.get_username()
            data["first_name"] = self.get_first_name(obj=instance)
            data["last_name"] = self.get_last_name(obj=instance)
            data["full_name"] = self.get_full_name(obj=instance)
            data["registration_time"] = instance.date_joined
            data["locale"] = "en"
            data["language_iso"] = "en"
            data["is_guest"] = False
            data["score"] = {"value": 0, "updated_at": None}
            return {k: v for k, v in data.items() if k in self.fields.keys()}

        return super().to_representation(instance)

    class Meta:
        model = TigaUser
        fields = (
            "uuid",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "registration_time",
            "locale",
            "language_iso",
            "is_guest",
            "score",
        )
        read_only_fields = (
            "registration_time",
            "score",
        )
        extra_kwargs = {
            "locale": {"default": "en"},
        }


class SimpleUserSerializer(UserSerializer):
    uuid = serializers.SerializerMethodField()

    def get_uuid(self, obj) -> UUID:
        return UUID(int=obj.pk)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ("uuid", "username", "first_name", "last_name", "full_name")


class MinimalUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = ("uuid", "locale")


#### START NOTIFICATION SERIALIZERS ####
class NotificationSerializer(serializers.ModelSerializer):
    class NotificationMessageSerializer(serializers.ModelSerializer):
        # Localized results
        title = serializers.SerializerMethodField()
        body = serializers.SerializerMethodField()

        def get_title(self, obj: NotificationContent) -> str:
            language_code = "en"
            user = self.context.get("request").user
            if user and isinstance(user, TigaUser):
                language_code = user.locale

            return obj.get_title(language_code=language_code)

        @extend_schema_field(HTMLCharField)
        def get_body(self, obj: NotificationContent) -> str:
            language_code = "en"
            user = self.context.get("request").user
            if user and isinstance(user, TigaUser):
                language_code = user.locale

            body_html = obj.get_body_html(language_code=language_code)

            return minify_html.minify(
                body_html or "",
                keep_closing_tags=True,
            )

        class Meta:
            model = NotificationContent
            fields = ("title", "body")

    message = NotificationMessageSerializer(
        source="notification.notification_content", read_only=True
    )
    created_at = serializers.DateTimeField(
        source="notification.date_comment", read_only=True
    )
    is_read = serializers.BooleanField(required=True)

    class Meta:
        model = NotificationRecipient
        fields = ("id", "message", "is_read", "created_at")
        read_only_fields = ("created_at",)
        extra_kwargs = {
            "id": {"source": "notification_id", "read_only": True},
        }


#### END NOTIFICATION SERIALIZERS ####


#### START MESSAGE SERIALIZERS ####
class MessageSerializer(serializers.ModelSerializer):
    class MessageContentSerializer(serializers.ModelSerializer):
        class LocalizedMessageTitleSerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        class LocalizedMessageBodySerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        title = LocalizedMessageTitleSerializer(
            source="*.title",
            max_length=255,
            help_text="Provide the message's title in all supported languages",
        )
        body = LocalizedMessageBodySerializer(
            source="*.body_html",
            is_html=True,
            help_text="Provide the message's body in all supported languages",
        )

        def validate_title(self, data):
            if data is None or data == {}:
                raise serializers.ValidationError("Title cannot be empty.")

            return data

        def validate_body(self, data):
            if data is None or data == {}:
                raise serializers.ValidationError("Body cannot be empty.")
            return data

        class Meta:
            model = NotificationContent
            fields = ("title", "body")

    created_at = serializers.DateTimeField(source="date_comment", read_only=True)

    sender_user_hidden_obj = serializers.HiddenField(
        source="expert", default=serializers.CurrentUserDefault()
    )
    sender_user = SimpleUserSerializer(source="expert", read_only=True)

    content = MessageContentSerializer(
        source="notification_content",
        required=True,
        help_text="The content of the message",
    )

    @transaction.atomic
    def create(self, validated_data) -> Notification:
        validated_data["notification_content"] = NotificationContent.objects.create(
            **validated_data.pop("notification_content")
        )
        return super().create(validated_data)

    class Meta:
        model = Notification
        fields = (
            "id",
            "sender_user",
            "sender_user_hidden_obj",
            "content",
            "created_at",
        )


class CreateUserMessageSerializer(MessageSerializer):
    user_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        allow_empty=False,
        min_length=1,
        write_only=True,
    )

    def validate(self, data):
        user_uuids = data.pop("user_uuids")
        users = TigaUser.objects.filter(pk__in=user_uuids)
        if users.count() != len(user_uuids):
            raise serializers.ValidationError("Some users were not found.")
        data["users"] = users
        return data

    def create(self, validated_data) -> Notification:
        users = validated_data.pop("users")
        notification = super().create(validated_data)
        for user in users:
            notification.send_to_user(user=user)

        return notification

    class Meta(MessageSerializer.Meta):
        fields = ("user_uuids",) + MessageSerializer.Meta.fields


class CreateTopicMessageSerializer(MessageSerializer):
    class CreateTopicMessageContentSerializer(serializers.ModelSerializer):
        class LocalizedTopicMessageTitleSerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        class LocalizedTopicMessageBodySerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        title = LocalizedTopicMessageTitleSerializer(
            source="*.title",
            required_languages=[
                "en"
            ],  # For topic messages, english is required as fallback if user locale is not supported.
            max_length=255,
            help_text="Provide the message's title in all supported languages for this topic",
        )
        body = LocalizedTopicMessageBodySerializer(
            source="*.body_html",
            required_languages=[
                "en"
            ],  # For topic messages, english is required as fallback if user locale is not supported.
            help_text="Provide the message's body in all supported languages for this topic",
        )

        class Meta:
            model = NotificationContent
            fields = ("title", "body")

    content = CreateTopicMessageContentSerializer(
        source="notification_content",
        required=True,
        help_text="The content of the message for the topic",
    )

    def create(self, validated_data) -> Notification:
        topic = self.context.get("topic")

        notification = super().create(validated_data)
        notification.send_to_topic(topic=topic)

        return notification


class MessageRecipientSerializer(serializers.ModelSerializer):
    user = MinimalUserSerializer(read_only=True)
    has_read = serializers.BooleanField(source="is_read", read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = ("user", "has_read")


class MessageTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTopic
        fields = ("code", "description")
        extra_kwargs = {
            "code": {"source": "topic_code"},
            "description": {"source": "topic_description"},
        }


#### END MESSAGE SERIALIZERS ####


class PartnerSerializer(serializers.ModelSerializer):
    point = PointField(required=True)

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
        source="photo",
        use_url=True,
        read_only=True,
        help_text="URL of the photo associated with the item. Note: This URL may change over time. Do not rely on it for permanent storage.",
    )

    class Meta:
        model = Photo
        fields = ("uuid", "url")
        read_only_fields = ("uuid",)


class BaseReportSerializer(TaggitSerializer, serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop("exclude_fields", None)
        super().__init__(*args, **kwargs)

        if exclude_fields:
            for field in exclude_fields:
                self.fields.pop(field, None)

    class LocationSerializer(serializers.ModelSerializer):
        class AdmBoundarySerializer(serializers.Serializer):
            name = serializers.CharField(required=True, allow_null=False)
            code = serializers.CharField(required=True, allow_null=False)
            source = serializers.CharField(required=True, allow_null=False)
            level = serializers.IntegerField(required=True, min_value=0)

        class PointSerializer(serializers.Serializer):
            latitude = WritableSerializerMethodField(
                field_class=serializers.FloatField,
                required=True,
            )
            longitude = WritableSerializerMethodField(
                field_class=serializers.FloatField,
                required=True,
            )

            def _round_value(self, value: float) -> float:
                try:
                    geo_precision = self.context.get("request").query_params.get(
                        "geo_precision"
                    )
                except Exception:
                    geo_precision = None
                return (
                    value if geo_precision is None else round(value, int(geo_precision))
                )

            def get_latitude(self, obj: Point) -> float:
                return self._round_value(obj.y)

            def get_longitude(self, obj: Point) -> float:
                return self._round_value(obj.x)

        point = PointSerializer(required=True)
        timezone = TimeZoneSerializerChoiceField(read_only=True, allow_null=True)
        country = CountrySerializer(read_only=True, allow_null=True)
        adm_boundaries = AdmBoundarySerializer(many=True, read_only=True)
        display_name = serializers.SerializerMethodField()
        source = serializers.ChoiceField(
            source="location_choice",
            choices=[("auto", "Auto (GPS)"), ("manual", "Manual (User-selected)")],
            help_text="Indicates how the location was obtained. Use 'Auto (GPS)' if the location was automatically retrieved"
            " from the device's GPS, or 'Manual (User-selected)' if the location was selected by the user on a map.",
        )

        def get_display_name(self, obj) -> Optional[str]:
            return obj.location_display_name

        def to_internal_value(self, data):
            ret = super().to_internal_value(data)

            # Map 'current' to 'auto' and 'selected' to 'manual'
            location_choice = data.get("source")

            if location_choice == "auto":
                ret["location_choice"] = Report.LOCATION_CURRENT
                preffix = "current"
            elif location_choice == "manual":
                ret["location_choice"] = Report.LOCATION_SELECTED
                preffix = "selected"

            point = ret.pop("point")
            ret[f"{preffix}_location_lat"] = point["latitude"]
            ret[f"{preffix}_location_lon"] = point["longitude"]

            return ret

        def to_representation(self, instance):
            ret = super().to_representation(instance)

            if self.allow_null and not instance.point:
                return None

            # Map 'current' to 'auto' and 'selected' to 'manual'
            location_choice = instance.location_choice
            ret["source"] = "auto"
            if location_choice == Report.LOCATION_SELECTED:
                ret["source"] = "manual"

            # Populating boundaries
            boundaries = []
            if instance.nuts_2_fk:
                boundaries.append(
                    {
                        "source": NutsEurope.SOURCE_NAME,
                        "code": instance.nuts_2_fk.code,
                        "name": instance.nuts_2_fk.name,
                        "level": instance.nuts_2_fk.level,
                    }
                )
            if instance.nuts_3_fk:
                boundaries.append(
                    {
                        "source": NutsEurope.SOURCE_NAME,
                        "code": instance.nuts_3_fk.code,
                        "name": instance.nuts_3_fk.name,
                        "level": instance.nuts_3_fk.level,
                    }
                )
            if instance.lau_fk:
                boundaries.append(
                    {
                        "source": LauEurope.SOURCE_NAME,
                        "code": instance.lau_fk.code,
                        "name": instance.lau_fk.name,
                        "level": instance.lau_fk.level,
                    }
                )
            ret["adm_boundaries"] = boundaries

            return ret

        class Meta:
            model = Report
            fields = (
                "source",
                "point",
                "timezone",
                "display_name",
                "country",
                "adm_boundaries",
            )

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
        help_text="The date and time when the record was created, displayed without timezone field."
    )
    sent_at = TimezoneAwareDateTimeField(required=True, source="phone_upload_time")
    published = serializers.SerializerMethodField()

    received_at = serializers.DateTimeField(read_only=True, source="server_upload_time")

    location = LocationSerializer(source="*")
    tags = TagListSerializerField(required=False, allow_empty=True)
    note = WritableSerializerMethodField(
        field_class=serializers.CharField,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def get_created_at_local(self, obj) -> datetime:
        return obj.creation_time_local.replace(tzinfo=None)

    def get_published(self, obj) -> bool:
        return obj.published

    def get_note(self, obj) -> Optional[str]:
        # Return the note if the user is allowed to see it.
        if not self.context.get("hide_note_if_not_owner", True):
            return obj.note

        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return None

        # Owner always sees it
        if request.user.pk == obj.user_id:
            return obj.note

        return None

    # Override from TaggitSerializer
    def _pop_tags(self, validated_data):
        tags, validated_data = super()._pop_tags(validated_data)

        # Also extract tags from note field
        note = validated_data.get("note", "")
        note_tags = Report.get_tags_from_note(note or "")
        tags["tags"] = list(set(tags.get("tags", []) + note_tags))

        return tags, validated_data

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
        extra_kwargs = {
            "uuid": {"required": True}  # Marks it as required in the response
        }


class BaseReportGeoModelSerializer(serializers.ModelSerializer):
    point = BaseReportSerializer.LocationSerializer.PointSerializer()
    uuid = BaseReportSerializer().fields["uuid"]
    received_at = BaseReportSerializer().fields["received_at"]

    class Meta:
        model = Report
        fields = (
            "uuid",
            "point",
            "received_at",
        )


class BaseSimplifiedReportSerializer(serializers.ModelSerializer):
    class SimplifiedLocationSerializer(serializers.ModelSerializer):
        point = BaseReportSerializer.LocationSerializer().fields["point"]
        timezone = BaseReportSerializer.LocationSerializer().fields["timezone"]
        display_name = BaseReportSerializer.LocationSerializer().fields["display_name"]
        country = BaseReportSerializer.LocationSerializer().fields["country"]

        get_display_name = BaseReportSerializer.LocationSerializer.get_display_name

        class Meta:
            model = BaseReportSerializer.LocationSerializer.Meta.model
            fields = ("point", "timezone", "display_name", "country")
            read_only_fields = fields

    uuid = BaseReportSerializer().fields["uuid"]
    short_id = BaseReportSerializer().fields["short_id"]
    # NOTE: user_uuid is used by AIMA for knowing who to send notifications.
    user_uuid = BaseReportSerializer().fields["user_uuid"]
    created_at = BaseReportSerializer().fields["created_at"]
    created_at_local = BaseReportSerializer().fields["created_at_local"]
    received_at = BaseReportSerializer().fields["received_at"]
    location = SimplifiedLocationSerializer(
        source=BaseReportSerializer().fields["location"].source
    )
    note = BaseReportSerializer().fields["note"]

    get_created_at_local = BaseReportSerializer.get_created_at_local
    get_note = BaseReportSerializer.get_note

    class Meta:
        model = BaseReportSerializer.Meta.model
        fields = (
            "uuid",
            "short_id",
            "user_uuid",
            "created_at",
            "created_at_local",
            "received_at",
            "location",
            "note",
        )
        read_only_fields = fields


class BaseReportWithPhotosSerializer(BaseReportSerializer):
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        # Use different field behavior depending on request method
        if request and request.method in ("POST", "PUT", "PATCH"):
            # Write mode — accept uploaded image files
            fields["photos"] = serializers.ListField(
                child=serializers.ImageField(required=True),
                write_only=True,
                min_length=1,
            )
        else:
            # Read mode — return nested photo serializer
            fields["photos"] = SimplePhotoSerializer(many=True, read_only=True)

        return fields

    @transaction.atomic
    def create(self, validated_data):
        photos = validated_data.pop("photos", [])

        instance = super().create(validated_data)

        # NOTE: do not use bulk here.
        for photo in photos:
            _ = Photo.objects.create(report=instance, photo=photo)

        return instance

    def to_representation(self, instance):
        """
        Always serialize output using the read-only `photos` definition,
        even if this serializer was initialized in write mode.
        """
        # Rebind `photos` temporarily for output
        if "photos" in self.fields:  # NOTE: csv render remove lists (and so 'photos')
            self.fields["photos"] = SimplePhotoSerializer(many=True, read_only=True)
        return super().to_representation(instance)

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + ("photos",)


class BaseSimplifiedReportSerializerWithPhoto(BaseSimplifiedReportSerializer):
    photos = BaseReportWithPhotosSerializer().fields["photos"]

    class Meta(BaseSimplifiedReportSerializer.Meta):
        fields = BaseSimplifiedReportSerializer.Meta.fields + ("photos",)
        read_only_fields = BaseSimplifiedReportSerializer.Meta.read_only_fields + (
            "photos",
        )


class SimpleTaxonSerializer(serializers.ModelSerializer):
    rank = serializers.ChoiceField(
        choices=[x.lower() for x in Taxon.TaxonomicRank.names]
    )

    italicize = serializers.SerializerMethodField(
        help_text="Display the name in italics when rendering."
    )

    def get_italicize(self, obj) -> bool:
        return obj.italicize

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["rank"] = [
            x.name.lower() for x in Taxon.TaxonomicRank if x.value == instance.rank
        ][0]
        return ret

    class Meta:
        model = Taxon
        fields = ("id", "name", "common_name", "rank", "italicize")
        extra_kwargs = {"id": {"read_only": True}}


class TaxonSerializer(SimpleTaxonSerializer):
    class Meta(SimpleTaxonSerializer.Meta):
        fields = SimpleTaxonSerializer.Meta.fields + ("is_relevant",)
        extra_kwargs = {"is_relevant": {"required": True}}


class TaxonTreeNodeSerializer(TaxonSerializer):
    children = serializers.SerializerMethodField()

    @extend_schema_field(
        lazy_serializer("mosquito_alert.api.v1.serializers.TaxonTreeNodeSerializer")(
            many=True
        )
    )
    def get_children(self, obj: Taxon):
        if obj.get_children_count():
            # TODO: get_children() -> can be improved to reduce the number of queries.
            return TaxonTreeNodeSerializer(obj.get_children(), many=True).data
        else:
            return []

    class Meta(TaxonSerializer.Meta):
        fields = TaxonSerializer.Meta.fields + ("children",)


class SimplifiedObservationSerializer(BaseSimplifiedReportSerializer):
    class Meta(BaseSimplifiedReportSerializer.Meta):
        pass


class SimplifiedObservationWithPhotosSerializer(
    BaseSimplifiedReportSerializerWithPhoto
):
    class Meta(BaseSimplifiedReportSerializerWithPhoto.Meta):
        pass


class SimpleAnnotatorUserSerializer(SimpleUserSerializer):
    def to_representation(self, instance):
        # Get the request user
        user = self.context.get("request").user
        # Check if the user has permission to view
        new_instance = instance
        if instance.pk != user.pk and not user.has_perm(
            "%(app_label)s.view_%(model_name)s"
            % {
                "app_label": UserStat._meta.app_label,
                "model_name": UserStat._meta.model_name,
            }
        ):
            new_instance = User(
                id=0, username="expert", first_name="Expert", last_name="Annotator"
            )

        return super().to_representation(new_instance)


class SpeciesIdentificationSerializer(serializers.ModelSerializer):
    class SpeciesClassificationSerializer(serializers.ModelSerializer):
        taxon = SimpleTaxonSerializer(read_only=True)
        confidence_label = WritableSerializerMethodField(
            field_class=serializers.ChoiceField,
            source="confidence",
            choices=ExpertReportAnnotation.ConfidenceCategory.labels,
            required=True,
        )
        is_high_confidence = serializers.SerializerMethodField()

        @extend_schema_field(
            serializers.ChoiceField(
                choices=ExpertReportAnnotation.ConfidenceCategory.labels
            )
        )
        def get_confidence_label(self, obj) -> str:
            if obj.confidence == 1:
                return ExpertReportAnnotation.ConfidenceCategory.DEFINITELY.label
            return ExpertReportAnnotation.ConfidenceCategory.PROBABLY.label

        def get_is_high_confidence(self, obj) -> bool:
            return obj.is_high_confidence

        def to_internal_value(self, data):
            if self.allow_null and data is None:
                return {"status": ExpertReportAnnotation.Status.HIDDEN}
            ret = super().to_internal_value(data)
            ret["confidence"] = next(
                val
                for val, lab in ExpertReportAnnotation.ConfidenceCategory.choices
                if lab == ret["confidence"]
            )
            return ret

        def to_representation(self, instance):
            if self.allow_null and instance.taxon is None:
                return None

            ret = super().to_representation(instance)

            return ret

        class Meta:
            model = ExpertReportAnnotation
            fields = (
                "taxon_id",
                "taxon",
                "confidence",
                "confidence_label",
                "is_high_confidence",
            )
            extra_kwargs = {
                "taxon_id": {
                    "source": "taxon",
                    "write_only": True,
                    "required": True,
                    "allow_null": False,
                },
                "confidence": {"read_only": True},
            }

    class SpeciesCharacteristicsSerializer(serializers.Serializer):
        sex = serializers.ChoiceField(choices=["male", "female"], required=True)
        is_blood_fed = serializers.BooleanField(required=False, allow_null=True)
        is_gravid = serializers.BooleanField(required=False, allow_null=True)

        def validate(self, data):
            if data.get("sex") == "male" and (
                data.get("is_blood_fed") or data.get("is_gravid")
            ):
                raise serializers.ValidationError(
                    "Male mosquitoes cannot be blood-fed or gravid."
                )
            return data

        def to_internal_value(self, data):
            if self.allow_null and data is None:
                return {
                    "sex": None,
                    "is_blood_fed": None,
                    "is_gravid": None,
                }
            return super().to_internal_value(data)

        def to_representation(self, instance):
            if self.allow_null and instance.sex is None:
                return None

            return super().to_representation(instance)

        class Meta:
            fields = ("sex", "is_blood_fed", "is_gravid")

    classification = SpeciesClassificationSerializer(
        source="*", required=True, allow_null=True
    )
    characteristics = SpeciesCharacteristicsSerializer(
        source="*", required=False, allow_null=True
    )

    def validate(self, data):
        characteristic_keys = self.fields["characteristics"].data.keys()
        if data.get("taxon") is None and any(
            data.get(key) is not None for key in characteristic_keys
        ):
            raise serializers.ValidationError(
                "Characteristics can not be set if taxon is not set."
            )

        return data

    class Meta:
        model = ExpertReportAnnotation
        fields = ("classification", "characteristics")


class AnnotationSerializer(SpeciesIdentificationSerializer):
    class AnnotationFeedbackSerializer(serializers.ModelSerializer):
        class Meta:
            model = ExpertReportAnnotation
            fields = ("public_note", "internal_note", "user_note")
            extra_kwargs = {
                "user_note": {"source": "message_for_user"},
            }

    class ObservationFlagsSerializer(serializers.ModelSerializer):
        is_favourite = serializers.BooleanField(required=False, default=False)
        is_visible = WritableSerializerMethodField(
            field_class=serializers.BooleanField,
            default=True,
        )

        def get_is_visible(self, obj) -> bool:
            return obj.status != ExpertReportAnnotation.Status.HIDDEN

        class Meta:
            model = ExpertReportAnnotation
            fields = ("is_favourite", "is_visible")

    observation_uuid = serializers.UUIDField(
        source="identification_task_id", read_only=True
    )
    user_hidden_obj = serializers.HiddenField(default=serializers.CurrentUserDefault())

    user = SimpleAnnotatorUserSerializer(read_only=True)
    feedback = AnnotationFeedbackSerializer(source="*", required=False)

    best_photo_uuid = serializers.UUIDField(write_only=True, required=False)
    best_photo = SimplePhotoSerializer(read_only=True, allow_null=True)
    tags = TagListSerializerField(required=False, allow_empty=True)
    type = serializers.SerializerMethodField()
    observation_flags = ObservationFlagsSerializer(source="*", required=False)

    is_flagged = WritableSerializerMethodField(
        field_class=serializers.BooleanField, default=False
    )

    is_executive = serializers.BooleanField(write_only=True, default=False)

    def get_type(self, obj) -> Literal["short", "long"]:
        return "short" if obj.is_simplified else "long"

    def get_is_flagged(self, obj) -> bool:
        return obj.status == ExpertReportAnnotation.Status.FLAGGED

    def validate(self, data):
        data = super().validate(data)

        data["user"] = data.pop("user_hidden_obj")
        data["is_finished"] = True

        try:
            data["identification_task"] = IdentificationTask.objects.get(
                pk=self.context.get("observation_uuid")
            )
        except IdentificationTask.DoesNotExist:
            raise serializers.ValidationError(
                "There is no identification task associated with the observation."
            )

        if best_photo_uuid := data.pop("best_photo_uuid", None):
            try:
                data["best_photo"] = Photo.objects.get(
                    report=data["identification_task"].report, uuid=best_photo_uuid
                )
            except Photo.DoesNotExist:
                raise serializers.ValidationError(
                    "The photo does not exist or does not belong to the observation."
                )

        is_flagged = data.pop("is_flagged")
        is_visible = data.pop(
            "is_visible", self.ObservationFlagsSerializer().fields["is_visible"].default
        )
        # Only if status not set yet (for example classification None sets it to hidden).
        if not data.get("status", None):
            if not is_visible:
                data["status"] = ExpertReportAnnotation.Status.HIDDEN
            elif is_flagged:
                data["status"] = ExpertReportAnnotation.Status.FLAGGED
            else:
                data["status"] = ExpertReportAnnotation.Status.PUBLIC

        data["decision_level"] = (
            ExpertReportAnnotation.DecisionLevel.EXECUTIVE
            if data.pop("is_executive", False)
            else ExpertReportAnnotation.DecisionLevel.NORMAL
        )
        user_role = data["user"]
        if isinstance(user_role, User):
            try:
                user_role = user_role.userstat
            except UserStat.DoesNotExist:
                user_role = None
        can_set_is_executive = False
        if user_role:
            can_set_is_executive = user_role.has_role_permission_by_model(
                action="mark_as_executive",
                model=ExpertReportAnnotation,
                country=data["identification_task"].report.country,
            )
        if not can_set_is_executive:
            data["decision_level"] = ExpertReportAnnotation.DecisionLevel.NORMAL
        return data

    class Meta:
        model = ExpertReportAnnotation
        fields = (
            (
                "id",
                "observation_uuid",
                "user_hidden_obj",
                "user",
                "best_photo_uuid",
                "best_photo",
            )
            + SpeciesIdentificationSerializer.Meta.fields
            + (
                "feedback",
                "type",
                "is_flagged",
                "is_executive",
                "decision_level",
                "observation_flags",
                "tags",
                "created_at",
                "updated_at",
            )
        )
        extra_kwargs = {
            "user_id": {"read_only": True},
            "created_at": {"source": "created", "read_only": True},
            "updated_at": {"source": "last_modified", "read_only": True},
            "decision_level": {"read_only": True},
        }


class BaseAssignmentSerializer(serializers.ModelSerializer):
    annotation_type = serializers.SerializerMethodField()

    def get_annotation_type(self, obj) -> Literal["short", "long"]:
        return "short" if obj.is_simplified else "long"

    class Meta:
        model = ExpertReportAnnotation
        fields = ("annotation_type",)


class AssignmentSerializer(BaseAssignmentSerializer):
    class AssignedObservationSerializer(SimplifiedObservationWithPhotosSerializer):
        user = MinimalUserSerializer(read_only=True)

        class Meta(SimplifiedObservationWithPhotosSerializer.Meta):
            fields = tuple(
                fname
                for fname in SimplifiedObservationWithPhotosSerializer.Meta.fields
                if fname != "user_uuid"
            ) + ("user",)

    observation = serializers.SerializerMethodField()

    @extend_schema_field(AssignedObservationSerializer)
    def get_observation(self, obj: ExpertReportAnnotation) -> dict:
        serializer = type(self).AssignedObservationSerializer(
            obj.identification_task.report,
            context={
                **self.context,
                "hide_note_if_not_owner": False,
            },  # always show note
        )
        return serializer.data

    class Meta(BaseAssignmentSerializer.Meta):
        fields = ("observation",) + BaseAssignmentSerializer.Meta.fields


class IdentificationTaskSerializer(serializers.ModelSerializer):
    class IdentificationTaskReviewSerializer(serializers.ModelSerializer):
        action = serializers.ChoiceField(
            source="review_type", choices=IdentificationTask.Review.choices
        )

        def to_representation(self, instance):
            if self.allow_null and instance.review_type is None:
                return None  # Return None or an empty dict as needed
            return super().to_representation(instance)

        class Meta:
            model = IdentificationTask
            fields = ("action", "created_at")
            extra_kwargs = {
                "created_at": {
                    "source": "reviewed_at",
                    "read_only": True,
                    "allow_null": False,
                },
            }

    class IdentificationTaskResultSerializer(serializers.ModelSerializer):
        taxon = SimpleTaxonSerializer(allow_null=True, read_only=True)
        confidence = serializers.FloatField(min_value=0, max_value=1, read_only=True)
        confidence_label = serializers.SerializerMethodField()
        is_high_confidence = serializers.SerializerMethodField()
        source = serializers.ChoiceField(
            source="result_source",
            read_only=True,
            choices=IdentificationTask.ResultSource.choices,
        )
        characteristics = (
            SpeciesIdentificationSerializer.SpeciesCharacteristicsSerializer(
                source="*", read_only=True, required=False, allow_null=True
            )
        )

        def get_confidence_label(self, obj) -> str:
            return obj.confidence_label

        def get_is_high_confidence(self, obj) -> bool:
            return obj.is_high_confidence

        def to_representation(self, instance):
            if self.allow_null and not instance.result_source:
                return None  # Return None or an empty dict as needed
            return super().to_representation(instance)

        class Meta:
            model = IdentificationTask
            fields = (
                "source",
                "taxon",
                "is_high_confidence",
                "confidence",
                "confidence_label",
                "uncertainty",
                "agreement",
                "characteristics",
            )
            extra_kwargs = {
                "confidence": {"min_value": 0, "max_value": 1},
                "uncertainty": {"min_value": 0, "max_value": 1},
                "agreement": {"min_value": 0, "max_value": 1},
            }

    class UserAssignmentSerializer(BaseAssignmentSerializer):
        user = SimpleAnnotatorUserSerializer()
        annotation_id = serializers.SerializerMethodField(allow_null=True)

        def get_annotation_id(self, obj) -> Optional[int]:
            return obj.pk if obj.is_finished else None

        class Meta(BaseAssignmentSerializer.Meta):
            fields = (
                "user",
                "annotation_id",
            ) + BaseAssignmentSerializer.Meta.fields

    observation = serializers.SerializerMethodField()
    public_photo_uuid = serializers.UUIDField(source="photo__uuid", write_only=True)
    public_photo = SimplePhotoSerializer(source="photo", read_only=True)
    review = IdentificationTaskReviewSerializer(
        source="*", allow_null=True, read_only=True
    )
    result = IdentificationTaskResultSerializer(
        source="*", read_only=True, allow_null=True
    )
    assignments = UserAssignmentSerializer(
        source="expert_report_annotations", many=True, read_only=True
    )

    @extend_schema_field(SimplifiedObservationWithPhotosSerializer)
    def get_observation(self, obj: IdentificationTask) -> dict:
        serializer = SimplifiedObservationWithPhotosSerializer(
            obj.report,
            context={
                **self.context,
                "hide_note_if_not_owner": False,
            },  # always show note
        )
        return serializer.data

    class Meta:
        model = IdentificationTask
        fields = (
            "observation",
            "public_photo_uuid",
            "public_photo",
            "assignments",
            "status",
            "is_flagged",
            "is_safe",
            "public_note",
            "num_annotations",
            "review",
            "result",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "status": {"default": IdentificationTask.Status.OPEN, "read_only": True},
            "public_note": {"allow_null": True, "allow_blank": True},
            "num_annotations": {"source": "total_finished_annotations", "min_value": 0},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
        }


class CreateReviewSerializer(serializers.Serializer):
    action = serializers.HiddenField(
        default=lambda field: field.context["request"].review_type, source="*"
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_action(self, value):
        return {}

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        ret["identification_task"] = self.context.get("identification_task")

        return ret

    class Meta:
        fields = (
            "action",
            "user",
        )


class CreateAgreeReviewSerializer(CreateReviewSerializer):
    action = serializers.ChoiceField(
        source="*", choices=[IdentificationTask.Review.AGREE.value]
    )

    def validate(self, data):
        data = super().validate(data)

        if data["identification_task"].is_reviewed:
            raise serializers.ValidationError(
                "This observation has already been reviewed. You can not agree with it."
            )

        return data

    def create(self, validated_data):
        identification_task = validated_data["identification_task"]
        identification_task.review_type = IdentificationTask.Review.AGREE
        identification_task.reviewed_at = timezone.now()
        identification_task.reviewed_by = validated_data["user"]
        identification_task.save()
        return identification_task

    class Meta(CreateReviewSerializer.Meta):
        pass


class CreateOverwriteReviewSerializer(
    CreateReviewSerializer, SpeciesIdentificationSerializer
):
    action = serializers.ChoiceField(
        source="*", choices=[IdentificationTask.Review.OVERWRITE.value]
    )
    is_safe = serializers.BooleanField(source="*", required=True)

    public_photo_uuid = serializers.UUIDField(source="photo__uuid", write_only=True)

    def validate_is_safe(self, value):
        return {"is_safe": value}

    def validate(self, data):
        data = super().validate(data)

        if public_photo_uuid := data.pop("photo__uuid", None):
            try:
                data["best_photo"] = Photo.objects.get(
                    report=data["identification_task"].report, uuid=public_photo_uuid
                )
            except Photo.DoesNotExist:
                raise serializers.ValidationError(
                    "The photo does not exist or does not belong to the observation."
                )

        return data

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)

        # Case Not an insect will be empty taxon. In case of update we need to for it to None
        ret["taxon"] = ret.pop("taxon", None)

        ret["is_finished"] = True
        ret["confidence"] = ret.pop("confidence", 0)

        ret["decision_level"] = ExpertReportAnnotation.DecisionLevel.FINAL
        ret["status"] = (
            ExpertReportAnnotation.Status.HIDDEN
            if not ret.pop("is_safe") or ret["taxon"] is None
            else ExpertReportAnnotation.Status.PUBLIC
        )
        ret["is_simplified"] = False

        return ret

    class Meta(CreateReviewSerializer.Meta):
        model = ExpertReportAnnotation
        fields = (
            CreateReviewSerializer.Meta.fields
            + (
                "public_photo_uuid",
                "is_safe",
                "public_note",
            )
            + SpeciesIdentificationSerializer.Meta.fields
        )
        extra_kwargs = {
            "public_note": {
                "required": True,
                "allow_null": True,
                "allow_blank": False,
                "read_only": False,
            }
        }


class ObservationGeoModelSerializer(BaseReportGeoModelSerializer):
    identification_taxon_id = serializers.ReadOnlyField(
        source="identification_task.taxon_id"
    )

    class Meta(BaseReportGeoModelSerializer.Meta):
        fields = BaseReportGeoModelSerializer.Meta.fields + ("identification_taxon_id",)


class ObservationGeoJsonModelSerializer(
    ReportGeoJsonModelSerializerMixin,
    ObservationGeoModelSerializer,
    GeoFeatureModelSerializer,
):
    class Meta(ObservationGeoModelSerializer.Meta):
        geo_field = "point"


class ObservationSerializer(BaseReportWithPhotosSerializer):
    class IdentificationSerializer(serializers.ModelSerializer):
        photo = SimplePhotoSerializer(required=True)
        result = IdentificationTaskSerializer.IdentificationTaskResultSerializer(
            source="*", allow_null=True, read_only=True
        )

        def to_representation(self, instance: IdentificationTask):
            ret = super().to_representation(instance)
            if self.allow_null and not instance.report.published:
                return None

            request = self.context.get("request")
            if (
                request
                and request.accepted_renderer.format == CSVStreamingRenderer.format
            ):
                if "public_note" in ret:
                    ret["public_note"] = None

            return ret

        class Meta:
            model = IdentificationTask
            fields = ("photo", "num_annotations", "result", "public_note")
            extra_kwargs = {
                "num_annotations": {
                    "source": "total_finished_annotations",
                    "min_value": 0,
                    "read_only": True,
                },
                "public_note": {"allow_null": True, "allow_blank": True},
            }

    identification = IdentificationSerializer(
        source="identification_task", read_only=True, allow_null=True
    )

    class MosquitoAppearanceSerializer(serializers.ModelSerializer):
        def to_representation(self, instance):
            ret = super().to_representation(instance)

            if self.allow_null:
                if not any(
                    [
                        instance.user_perceived_mosquito_specie,
                        instance.user_perceived_mosquito_thorax,
                        instance.user_perceived_mosquito_abdomen,
                        instance.user_perceived_mosquito_legs,
                    ]
                ):
                    return None

            return ret

        class Meta:
            model = Report
            fields = ("specie", "thorax", "abdomen", "legs")
            extra_kwargs = {
                "specie": {"source": "user_perceived_mosquito_specie"},
                "thorax": {"source": "user_perceived_mosquito_thorax"},
                "abdomen": {"source": "user_perceived_mosquito_abdomen"},
                "legs": {"source": "user_perceived_mosquito_legs"},
            }

    mosquito_appearance = MosquitoAppearanceSerializer(
        source="*",
        required=False,
        allow_null=True,
        help_text="User-provided description of the mosquito's appearance",
    )

    def create(self, validated_data):
        validated_data["type"] = Report.TYPE_ADULT
        return super().create(validated_data)

    class Meta(BaseReportWithPhotosSerializer.Meta):
        fields = BaseReportWithPhotosSerializer.Meta.fields + (
            "identification",
            "event_environment",
            "event_moment",
            "mosquito_appearance",
        )


class BiteGeoModelSerializer(BaseReportGeoModelSerializer):
    class Meta(BaseReportGeoModelSerializer.Meta):
        pass


class BiteGeoJsonModelSerializer(
    ReportGeoJsonModelSerializerMixin, BiteGeoModelSerializer, GeoFeatureModelSerializer
):
    class Meta(BiteGeoModelSerializer.Meta):
        geo_field = "point"


class BiteSerializer(BaseReportSerializer):
    class BiteCountsSerializer(serializers.ModelSerializer):
        total = IntegerDefaultField(
            default=0,
            source="bite_count",
            read_only=True,
            help_text=Report._meta.get_field("bite_count").help_text,
        )
        head = IntegerDefaultField(
            default=0,
            source="head_bite_count",
            help_text=Report._meta.get_field("head_bite_count").help_text,
        )
        left_arm = IntegerDefaultField(
            default=0,
            source="left_arm_bite_count",
            help_text=Report._meta.get_field("left_arm_bite_count").help_text,
        )
        right_arm = IntegerDefaultField(
            default=0,
            source="right_arm_bite_count",
            help_text=Report._meta.get_field("right_arm_bite_count").help_text,
        )
        chest = IntegerDefaultField(
            default=0,
            source="chest_bite_count",
            help_text=Report._meta.get_field("chest_bite_count").help_text,
        )
        left_leg = IntegerDefaultField(
            default=0,
            source="left_leg_bite_count",
            help_text=Report._meta.get_field("left_leg_bite_count").help_text,
        )
        right_leg = IntegerDefaultField(
            default=0,
            source="right_leg_bite_count",
            help_text=Report._meta.get_field("right_leg_bite_count").help_text,
        )

        class Meta:
            model = Report
            fields = (
                "total",
                "head",
                "left_arm",
                "right_arm",
                "chest",
                "left_leg",
                "right_leg",
            )

    counts = BiteCountsSerializer(source="*")

    def create(self, validated_data):
        validated_data["type"] = Report.TYPE_BITE
        return super().create(validated_data)

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + (
            "event_environment",
            "event_moment",
            "counts",
        )


class BreedingSiteSerializer(BaseReportWithPhotosSerializer):
    site_type = WritableSerializerMethodField(
        field_class=serializers.ChoiceField,
        choices=Report.BreedingSiteType.choices,
        source="breeding_site_type",
        required=True,
        allow_null=False,
        allow_blank=False,
    )

    def get_site_type(self, obj) -> Report.BreedingSiteType:
        return obj.breeding_site_type or Report.BreedingSiteType.OTHER

    def create(self, validated_data):
        validated_data["type"] = Report.TYPE_SITE
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
            # Need to set default to None, otherwise BooleanField uses False
            "has_water": {
                "allow_null": True,
                "default": None,
                "source": "breeding_site_has_water",
            },
            "in_public_area": {
                "allow_null": True,
                "default": None,
                "source": "breeding_site_in_public_area",
            },
            "has_near_mosquitoes": {
                "allow_null": True,
                "default": None,
                "source": "breeding_site_has_near_mosquitoes",
            },
            "has_larvae": {
                "allow_null": True,
                "default": None,
                "source": "breeding_site_has_larvae",
            },
        }


class BreedingSiteGeoModelSerializer(BaseReportGeoModelSerializer):
    site_type = BreedingSiteSerializer().fields["site_type"]
    has_water = BreedingSiteSerializer().fields["has_water"]

    get_site_type = BreedingSiteSerializer().get_site_type

    class Meta(BaseReportGeoModelSerializer.Meta):
        fields = BaseReportGeoModelSerializer.Meta.fields + ("site_type", "has_water")


class BreedingSiteGeoJsonModelSerializer(
    ReportGeoJsonModelSerializerMixin,
    BreedingSiteGeoModelSerializer,
    GeoFeatureModelSerializer,
):
    class Meta(BreedingSiteGeoModelSerializer.Meta):
        geo_field = "point"


#### END REPORT SERIALIZERS ####


class PhotoSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField(
        help_text="Internal server path of the image."
    )

    def get_image_path(self, obj) -> str:
        return obj.photo.path

    class Meta:
        model = Photo
        fields = ("uuid", "image_url", "image_path")
        extra_kwargs = {
            "uuid": {"required": True},
            "image_url": {"source": "photo"},
        }


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
        device = (
            Device.objects.filter(
                models.Q(model=model)
                | models.Q(registration_id=validated_data.get("registration_id"))
            )
            .filter(user=user, device_id=None)
            .first()
        )
        if device:
            Device.objects.filter(user=user, model=model, device_id=device_id).delete()
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


class PhotoPredictionSerializer(serializers.ModelSerializer):
    class BoundingBoxSerializer(serializers.ModelSerializer):
        class Meta:
            model = PhotoPrediction
            fields = (
                "x_min",
                "y_min",
                "x_max",
                "y_max",
            )
            extra_kwargs = {
                "x_min": {"source": "x_tl"},
                "y_min": {"source": "y_tl"},
                "x_max": {"source": "x_br"},
                "y_max": {"source": "y_br"},
            }

    class PredictionScoreSerializer(serializers.ModelSerializer):
        class Meta:
            model = PhotoPrediction
            fields = [
                fname.replace(PhotoPrediction.CLASS_FIELD_SUFFIX, "")
                for fname in PhotoPrediction.get_score_fieldnames()
            ]
            extra_kwargs = {
                fname.replace(PhotoPrediction.CLASS_FIELD_SUFFIX, ""): {"source": fname}
                for fname in PhotoPrediction.get_score_fieldnames()
            }

    photo = SimplePhotoSerializer(read_only=True)
    bbox = BoundingBoxSerializer(source="*")
    scores = PredictionScoreSerializer(source="*")
    taxon = SimpleTaxonSerializer(allow_null=True, read_only=True)

    class Meta:
        model = PhotoPrediction
        fields = (
            "photo",
            "bbox",
            "insect_confidence",
            "predicted_class",
            "taxon",
            "threshold_deviation",
            "is_decisive",
            "scores",
            "classifier_version",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {"predicted_class": {"required": True}}


class CreatePhotoPredictionSerializer(PhotoPredictionSerializer):
    photo_uuid = serializers.UUIDField(
        source="photo__uuid", required=True, write_only=True
    )

    def validate(self, data):
        data["identification_task_id"] = self.context.get("observation_uuid")
        photo__uuid = data.pop("photo__uuid")

        try:
            data["photo"] = Photo.objects.get(
                uuid=photo__uuid, report_id=data["identification_task_id"]
            )
        except Photo.DoesNotExist:
            raise serializers.ValidationError(
                "The selected photo does not belong to this identification task or does not exist."
            )

        return data

    class Meta(PhotoPredictionSerializer.Meta):
        fields = ("photo_uuid",) + PhotoPredictionSerializer.Meta.fields


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
