from datetime import datetime
from typing import Literal, Optional
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.helpers import lazy_serializer

from rest_framework import serializers

from drf_extra_fields.geo_fields import PointField
from taggit.serializers import TaggitSerializer

from tigacrafting.models import (
    IdentificationTask,
    Taxon,
    ExpertReportAnnotation,
    UserStat,
    PhotoPrediction,
    FavoritedReports
)
from tigaserver_app.models import (
    NotificationContent,
    Notification,
    OrganizationPin,
    OWCampaigns,
    EuropeCountry,
    LauEurope,
    NutsEurope,
    TigaUser,
    Report,
    Photo,
    Fix,
    NotificationTopic,
    Device,
    MobileApp
)

from .base_serializers import LocalizedSerializerMixin
from .fields import (
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    IntegerDefaultField,
    TagListSerializerField,
    TimeZoneSerializerChoiceField,
)

User = get_user_model()


class SimpleRegularUserSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'full_name'
        )
        extra_kwargs = {
            "id": {"read_only": True},
        }

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

class UserSerializer(serializers.ModelSerializer):
    class UserScoreSerializer(serializers.ModelSerializer):
        value = serializers.IntegerField(source="score_v2", min_value=0, read_only=True)
        updated_at = serializers.DateTimeField(source="last_score_update", read_only=True, allow_null=True)

        class Meta:
            model = TigaUser
            fields = ("value", "updated_at")

    uuid = serializers.UUIDField(source="user_UUID", read_only=True)
    language_iso = serializers.SerializerMethodField(help_text='ISO 639-1 code', default='en')
    username = serializers.SerializerMethodField()
    is_guest = serializers.SerializerMethodField()
    score = UserScoreSerializer(source='*', read_only=True)

    def get_is_guest(self, obj) -> bool:
        return True

    def get_username(self, obj) -> str:
        return obj.get_username()

    def get_language_iso(self, obj) -> str:
        return obj.language_iso2

    def to_representation(self, instance):
        if isinstance(instance, User):
            # NOTE: this must be the same structure as defined.
            data = {}
            data['uuid'] = uuid.UUID(int=instance.pk)
            data['username'] = instance.get_username()
            data['registration_time'] = instance.date_joined
            data['locale'] = 'en'
            data['language_iso'] = 'en'
            data['is_guest'] = False
            data['score'] = {
                'value': 0,
                'updated_at': None
            }
            return data

        return super().to_representation(instance)

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
        )
        read_only_fields = (
            "registration_time",
            "score",
        )
        extra_kwargs = {
            "locale": {"default": "en"},
        }

class SimpleUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = (
            "uuid",
            "locale"
        )

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
        class LocalizedMessageTitleSerializer(LocalizedSerializerMixin, serializers.Serializer):
            pass

        class LocalizedMessageBodySerializer(LocalizedSerializerMixin, serializers.Serializer):
            pass

        title = LocalizedMessageTitleSerializer(
            max_length=255,
            help_text="Provide the message's title in all supported languages"
        )
        body = LocalizedMessageBodySerializer(
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
    receiver_type = serializers.HiddenField(default=None)

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

    # NOTE: needed for drf-spectacular
    receiver_type = serializers.ChoiceField(choices=['user'], default='user', write_only=True)

    user_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        allow_empty=False,
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

    # NOTE: needed for drf-spectacular
    receiver_type = serializers.ChoiceField(choices=['topic'], default='topic', write_only=True)

    topic_codes = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
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
        class AdmBoundarySerializer(serializers.Serializer):
            name = serializers.CharField(required=True, allow_null=False)
            code = serializers.CharField(required=True, allow_null=False)
            source = serializers.CharField(required=True, allow_null=False)
            level = serializers.IntegerField(required=True, min_value=0)

        point = PointField(required=True)
        timezone = TimeZoneSerializerChoiceField(read_only=True, allow_null=True)
        country = CountrySerializer(read_only=True, allow_null=True)
        adm_boundaries = AdmBoundarySerializer(many=True, read_only=True)
        display_name = serializers.SerializerMethodField()
        source = serializers.ChoiceField(
            source="location_choice",
            choices=[('auto', 'Auto (GPS)'), ('manual', 'Manual (User-selected)')],
            help_text="Indicates how the location was obtained. Use 'Auto (GPS)' if the location was automatically retrieved"
            " from the device's GPS, or 'Manual (User-selected)' if the location was selected by the user on a map.")

        def get_display_name(self, obj) -> Optional[str]:
            return obj.location_display_name

        def to_internal_value(self, data):
            ret = super().to_internal_value(data)

            # Map 'current' to 'auto' and 'selected' to 'manual'
            location_choice = data.get('source')

            if location_choice == 'auto':
                ret['location_choice'] = Report.LOCATION_CURRENT
                preffix = "current"
            elif location_choice == 'manual':
                ret['location_choice'] = Report.LOCATION_SELECTED
                preffix = "selected"

            point = ret.pop("point")
            ret[f"{preffix}_location_lat"] = point.y
            ret[f"{preffix}_location_lon"] = point.x

            return ret

        def to_representation(self, instance):
            ret = super().to_representation(instance)

            if self.allow_null and not instance.point:
                return None

            # Map 'current' to 'auto' and 'selected' to 'manual'
            location_choice = instance.location_choice
            ret['source'] = 'auto'
            if location_choice == Report.LOCATION_SELECTED:
                ret['source'] = 'manual'

            # Populating boundaries
            boundaries = []
            if instance.nuts_2_fk:
                boundaries.append({
                    "source": NutsEurope.SOURCE_NAME,
                    "code": instance.nuts_2_fk.code,
                    "name": instance.nuts_2_fk.name,
                    "level": instance.nuts_2_fk.level,
                })
            if instance.nuts_3_fk:
                boundaries.append({
                    "source": NutsEurope.SOURCE_NAME,
                    "code": instance.nuts_3_fk.code,
                    "name": instance.nuts_3_fk.name,
                    "level": instance.nuts_3_fk.level,
                })
            if instance.lau_fk:
                boundaries.append({
                    "source": LauEurope.SOURCE_NAME,
                    "code": instance.lau_fk.code,
                    "name": instance.lau_fk.name,
                    "level": instance.lau_fk.level,
                })
            ret['adm_boundaries'] = boundaries

            return ret

        class Meta:
            model = Report
            fields = (
                "source",
                "point",
                "timezone",
                "display_name",
                "country",
                "adm_boundaries"
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
        help_text="The date and time when the record was created, displayed in the local timezone specified for this entry."
    )
    sent_at = TimezoneAwareDateTimeField(required=True, source="phone_upload_time")
    published = serializers.SerializerMethodField()

    received_at = serializers.DateTimeField(read_only=True, source="server_upload_time")

    location = LocationSerializer(source="*")
    tags = TagListSerializerField(required=False, allow_empty=True)

    def get_created_at_local(self, obj) -> datetime:
        return obj.creation_time_local

    def get_published(self, obj) -> bool:
        return obj.published

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

class BaseSimplifiedReportSerializer(serializers.ModelSerializer):
    class SimplifiedLocationSerializer(serializers.ModelSerializer):
        point = BaseReportSerializer.LocationSerializer().fields['point']
        timezone = BaseReportSerializer.LocationSerializer().fields['timezone']
        display_name = BaseReportSerializer.LocationSerializer().fields['display_name']
        country = BaseReportSerializer.LocationSerializer().fields['country']

        get_display_name = BaseReportSerializer.LocationSerializer.get_display_name

        class Meta:
            model = BaseReportSerializer.LocationSerializer.Meta.model
            fields = (
                "point",
                "timezone",
                "display_name",
                "country"
            )
            read_only_fields = fields

    uuid = BaseReportSerializer().fields['uuid']
    # NOTE: user_uuid is used by AIMA for knowing who to send notifications.
    user_uuid = BaseReportSerializer().fields['user_uuid']
    created_at = BaseReportSerializer().fields['created_at']
    created_at_local = BaseReportSerializer().fields['created_at_local']
    received_at = BaseReportSerializer().fields['received_at']
    location = SimplifiedLocationSerializer(source=BaseReportSerializer().fields['location'].source)
    note = BaseReportSerializer().fields['note']

    get_created_at_local = BaseReportSerializer.get_created_at_local

    class Meta:
        model = BaseReportSerializer.Meta.model
        fields = (
            "uuid",
            "user_uuid",
            "created_at",
            "created_at_local",
            "received_at",
            "location",
            "note",
        )
        read_only_fields = fields

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

class BaseSimplifiedReportSerializerWithPhoto(BaseSimplifiedReportSerializer):
    photos = BaseReportWithPhotosSerializer().fields['photos']
    class Meta(BaseSimplifiedReportSerializer.Meta):
        fields = BaseSimplifiedReportSerializer.Meta.fields + ('photos',)
        read_only_fields = BaseSimplifiedReportSerializer.Meta.read_only_fields + ('photos',)

class SimpleTaxonSerializer(serializers.ModelSerializer):
    rank = serializers.ChoiceField(choices=[x.lower() for x in Taxon.TaxonomicRank.names])

    italicize = serializers.SerializerMethodField(help_text="Display the name in italics when rendering.")

    def get_italicize(self, obj) -> bool:
        return obj.italicize

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['rank'] = [x.name.lower() for x in Taxon.TaxonomicRank if x.value == instance.rank][0]
        return ret

    class Meta:
        model = Taxon
        fields = (
            'id',
            'name',
            'common_name',
            'rank',
            'italicize'
        )
        extra_kwargs = {
            'id': {'read_only': True}
        }

class TaxonSerializer(SimpleTaxonSerializer):

    class Meta(SimpleTaxonSerializer.Meta):
        fields = SimpleTaxonSerializer.Meta.fields + (
            'is_relevant',
        )
        extra_kwargs = {
            'is_relevant': {'required': True}
        }

class TaxonTreeNodeSerializer(TaxonSerializer):
    children = serializers.SerializerMethodField()

    @extend_schema_field(lazy_serializer("api.serializers.TaxonTreeNodeSerializer")(many=True))
    def get_children(self, obj: Taxon):
        if obj.get_children_count():
            # TODO: get_children() -> can be improved to reduce the number of queries.
            return TaxonTreeNodeSerializer(obj.get_children(), many=True).data
        else:
            return []

    class Meta(TaxonSerializer.Meta):
        fields = TaxonSerializer.Meta.fields + (
            'children',
        )

class SimplifiedObservationSerializer(BaseSimplifiedReportSerializer):
    class Meta(BaseSimplifiedReportSerializer.Meta):
        pass

class SimplifiedObservationWithPhotosSerializer(BaseSimplifiedReportSerializerWithPhoto):
    class Meta(BaseSimplifiedReportSerializerWithPhoto.Meta):
        pass

class SimpleAnnotatorUserSerializer(SimpleRegularUserSerializer):
    def to_representation(self, instance):
        # Get the request user
        user = self.context.get('request').user
        # Check if the user has permission to view
        new_instance = instance
        if instance.pk != user.pk and not user.has_perm('%(app_label)s.view_%(model_name)s' % {
            'app_label': UserStat._meta.app_label,
            'model_name': UserStat._meta.model_name
        }):
            new_instance = User(id=-1, username='expert', first_name='Expert', last_name='Annotator')

        return super().to_representation(new_instance)

class AnnotationSerializer(serializers.ModelSerializer):
    class AnnotationFeedbackSerializer(serializers.ModelSerializer):
        def validate_public_note(self, value):
            # edited_user_notes can not be null, cast to blank.
            return value or ""

        def validate_internal_note(self, value):
            # tiger_certainty_notes can not be null, cast to blank.
            return value or ""

        def validate_user_note(self, value):
            # message_for_user can not be null, cast to blank.
            return value or ""

        def to_representation(self, instance):
            ret = super().to_representation(instance)
            # Ensure public_note and user_note will be None instead of blank
            ret['public_note'] = ret['public_note'] or None
            ret['internal_note'] = ret['internal_note'] or None
            ret['user_note'] = ret['user_note'] or None
            return ret

        class Meta:
            model = ExpertReportAnnotation
            fields = (
                "public_note",
                "internal_note",
                "user_note"
            )
            extra_kwargs = {
                "public_note": {"source": "edited_user_notes", "allow_null": True},
                "internal_note": {"source": "tiger_certainty_notes", "allow_null": True},
                "user_note": {"source": "message_for_user", "allow_null": True},
            }

    class AnnotationClassificationSerializer(serializers.ModelSerializer):
        taxon = SimpleTaxonSerializer(read_only=True)
        confidence_label = serializers.ChoiceField(
            source="validation_value",
            choices=['definitely', 'probably'],
            required=True
        )
        is_high_confidence = serializers.SerializerMethodField()

        def get_is_high_confidence(self, obj) -> bool:
            return obj.is_high_confidence

        def to_internal_value(self, data):
            if self.allow_null and data is None:
                return {
                    'status': ExpertReportAnnotation.STATUS_HIDDEN
                }
            ret = super().to_internal_value(data)
            ret['validation_value'] = ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY if data.pop('confidence_label') == 'definitely' else ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
            return ret

        def to_representation(self, instance):
            if self.allow_null and instance.taxon is None:
                return None

            ret = super().to_representation(instance)
            ret['confidence_label'] = 'definitely' if instance.validation_value == ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY else 'probably'

            return ret

        class Meta:
            model = ExpertReportAnnotation
            fields = (
                "taxon_id",
                "taxon",
                "confidence",
                "confidence_label",
                "is_high_confidence"
            )
            extra_kwargs = {
                "taxon_id": {"source": "taxon", "write_only": True, "required": True, "allow_null": False},
                "confidence": {"read_only": True},
            }

    class AnnotationCharacteristicsSerializer(serializers.Serializer):
        sex = serializers.ChoiceField(choices=['male', 'female'], required=False, allow_null=True)
        is_blood_fed = serializers.BooleanField(required=False, default=False)
        is_gravid = serializers.BooleanField(required=False, default=False)

        def to_internal_value(self, data):
            sex = data.pop('sex', None)
            is_blood_fed = data.pop('is_blood_fed', False)
            is_gravid = data.pop('is_gravid', False)

            ret = {}
            if sex == 'male':
                blood_genre = 'male'
            elif sex == 'female':
                if is_gravid and is_blood_fed:
                    blood_genre = 'fgblood'
                elif is_gravid:
                    blood_genre = 'fgravid'
                elif is_blood_fed:
                    blood_genre = 'fblood'
                else:
                    blood_genre = 'female'
            else:
                blood_genre = 'dk'

            ret['blood_genre'] = blood_genre
            return ret

        class Meta:
            fields = ("sex", "is_blood_fed", "is_gravid")

    user_hidden_obj = serializers.HiddenField(default=serializers.CurrentUserDefault())

    user = SimpleAnnotatorUserSerializer(read_only=True)
    feedback = AnnotationFeedbackSerializer(source='*', required=False)

    classification = AnnotationClassificationSerializer(source='*', required=True, allow_null=True)
    characteristics = AnnotationCharacteristicsSerializer(required=False, write_only=True)
    best_photo_uuid = serializers.UUIDField(write_only=True, required=False)
    best_photo = SimplePhotoSerializer(read_only=True, allow_null=True)
    tags = TagListSerializerField(required=False, allow_empty=True)
    type = serializers.SerializerMethodField()

    is_flagged = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        default=False
    )

    is_decisive = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        default=False,
    )

    is_favourite = WritableSerializerMethodField(
        field_class=serializers.BooleanField,
        default=False,
    )

    def get_type(self, obj) -> Literal['short', 'long']:
        return 'short' if obj.simplified_annotation else 'long'

    def get_is_flagged(self, obj) -> bool:
        return obj.status == ExpertReportAnnotation.STATUS_FLAGGED

    def get_is_decisive(self, obj) -> bool:
        return obj.validation_complete_executive or obj.revise

    def get_is_favourite(self, obj) -> bool:
        return obj.is_favourite

    def validate(self, data):
        data['user'] = data.pop('user_hidden_obj')
        data['validation_complete'] = True

        try:
            data['report'] = Report.objects.get(type='adult', pk=self.context.get('observation_uuid'))
        except Report.DoesNotExist:
            raise serializers.ValidationError("The observation does not does not exist.")

        if best_photo_uuid := data.pop('best_photo_uuid', None):
            try:
                data['best_photo'] = Photo.objects.get(report=data['report'], uuid=best_photo_uuid)
            except Photo.DoesNotExist:
                raise serializers.ValidationError("The photo does not does not exist or does not belong to the observation.")

        is_flagged = data.pop("is_flagged")
        if is_flagged:
            data["status"] = ExpertReportAnnotation.STATUS_FLAGGED
        elif not data.get("status", None):
            # Only set to PUBLIC if not set to HIDDEN
            data["status"] = ExpertReportAnnotation.STATUS_PUBLIC

        data['validation_complete_executive'] = data.pop("is_decisive")

        return data

    def create(self, validated_data):
        is_favourite = validated_data.pop("is_favourite", False)
        characteristics = validated_data.pop("characteristics", {})
        blood_genre = characteristics.get("blood_genre", None)
        with transaction.atomic():
            instance = super().create(validated_data)
            if is_favourite:
                FavoritedReports.objects.get_or_create(
                    user=instance.user,
                    report=instance.report,
                )
            if blood_genre and instance.best_photo:
                # Update the best photo with the blood_genre
                instance.best_photo.blood_genre = blood_genre
                instance.best_photo.save()

        return instance

    def update(self, instance, validated_data):
        is_favourite = validated_data.pop("is_favourite", False)
        characteristics = validated_data.pop("characteristics", {})
        blood_genre = characteristics.get("blood_genre", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if is_favourite:
                FavoritedReports.objects.get_or_create(
                    user=instance.user,
                    report=instance.report,
                )
            else:
                FavoritedReports.objects.filter(
                    user=instance.user,
                    report=instance.report,
                ).delete()
            if blood_genre and instance.best_photo:
                # Update the best photo with the blood_genre
                instance.best_photo.blood_genre = blood_genre
                instance.best_photo.save()
        return instance

    class Meta:
        model = ExpertReportAnnotation
        fields = (
            "id",
            "observation_uuid",
            "user_hidden_obj",
            "user",
            "best_photo_uuid",
            "best_photo",
            "classification",
            "characteristics",
            "feedback",
            "type",
            "is_flagged",
            "is_decisive",
            "is_favourite",
            "tags",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "user_id": {'read_only': True},
            "observation_uuid": {'source': 'report', 'read_only': True},
            'created_at': {"source": "created", 'read_only': True},
            'updated_at': {"source": "last_modified", 'read_only': True},
        }

class SimpleAnnotationSerializer(serializers.ModelSerializer):
    id = AnnotationSerializer().fields['id']
    user = AnnotationSerializer().fields['user']
    classification = AnnotationSerializer().fields['classification']
    is_flagged = AnnotationSerializer().fields['is_flagged']
    is_decisive = AnnotationSerializer().fields['is_decisive']

    get_is_flagged = AnnotationSerializer.get_is_flagged
    get_is_decisive = AnnotationSerializer.get_is_decisive

    class Meta:
        model = AnnotationSerializer.Meta.model
        fields = (
            "id",
            "user",
            "classification",
            "is_flagged",
            "is_decisive"
        )

class BaseAssignmentSerializer(serializers.ModelSerializer):
    annotation_type = serializers.SerializerMethodField()

    def get_annotation_type(self, obj) -> Literal['short', 'long']:
        return 'short' if obj.simplified_annotation else 'long'

    class Meta:
        model = ExpertReportAnnotation
        fields = ('annotation_type',)

class AssignmentSerializer(BaseAssignmentSerializer):
    class AssignedObservationSerializer(SimplifiedObservationWithPhotosSerializer):
        user = SimpleUserSerializer(read_only=True)
        class Meta(SimplifiedObservationWithPhotosSerializer.Meta):
            fields = tuple(
                fname for fname in SimplifiedObservationWithPhotosSerializer.Meta.fields if fname != 'user_uuid'
            ) + ("user",)

    observation = AssignedObservationSerializer(source='report', read_only=True)
    class Meta(BaseAssignmentSerializer.Meta):
        fields = ('observation', ) + BaseAssignmentSerializer.Meta.fields

class IdentificationTaskSerializer(serializers.ModelSerializer):
    class IdentificationTaskReviewSerializer(serializers.ModelSerializer):
        type = serializers.ChoiceField(source='review_type',choices=IdentificationTask.Review.choices)

        def to_representation(self, instance):
            if self.allow_null and instance.review_type is None:
                return None  # Return None or an empty dict as needed
            return super().to_representation(instance)

        class Meta:
            model = IdentificationTask
            fields = (
                "type",
                "created_at"
            )
            extra_kwargs = {
                'created_at': {'source': 'reviewed_at', 'read_only': True},
            }

    class IdentificationTaskResultSerializer(serializers.ModelSerializer):
        taxon = SimpleTaxonSerializer(allow_null=True, read_only=True)
        confidence = serializers.FloatField(min_value=0, max_value=1, read_only=True)
        confidence_label = serializers.SerializerMethodField()
        is_high_confidence = serializers.SerializerMethodField()
        source = serializers.ChoiceField(source='result_source',choices=IdentificationTask.ResultSource.choices, allow_null=True)

        def get_confidence_label(self, obj) -> str:
            return obj.confidence_label

        def get_is_high_confidence(self, obj) -> bool:
            return obj.is_high_confidence

        def to_representation(self, instance):
            if self.allow_null and not instance.is_done:
                return None  # Return None or an empty dict as needed
            return super().to_representation(instance)

        class Meta:
            model = IdentificationTask
            fields = (
                'source',
                'taxon',
                'is_high_confidence',
                'confidence',
                'confidence_label',
                'uncertainty',
                'agreement',
            )
            extra_kwargs = {
                'confidence': {'min_value': 0, 'max_value': 1},
                'uncertainty': {'min_value': 0, 'max_value': 1},
                'agreement': {'min_value': 0, 'max_value': 1},
            }

    class UserAssignmentSerializer(BaseAssignmentSerializer):
        user = SimpleAnnotatorUserSerializer()
        annotation_id = serializers.SerializerMethodField(allow_null=True)

        def get_annotation_id(self, obj) -> Optional[int]:
            return obj.pk if obj.validation_complete else None

        class Meta(BaseAssignmentSerializer.Meta):
            fields = ("user", "annotation_id",) + BaseAssignmentSerializer.Meta.fields

    observation = SimplifiedObservationWithPhotosSerializer(source='report', read_only=True)
    public_photo = SimplePhotoSerializer(source='photo', required=True)
    review = IdentificationTaskReviewSerializer(source='*', allow_null=True, read_only=True)
    result = IdentificationTaskResultSerializer(source='*', read_only=True)
    assignments = UserAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = IdentificationTask
        fields = (
            'observation',
            'public_photo',
            'assignments',
            'status',
            'is_flagged',
            'is_safe',
            'public_note',
            'num_annotations',
            'review',
            'result',
            'created_at',
            'updated_at'
        )
        extra_kwargs = {
            'status': {'default': IdentificationTask.Status.OPEN},
            'public_note': {'allow_null': True, 'allow_blank': True},
            'num_annotations': {'source': 'total_finished_annotations','min_value': 0},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

class ObservationSerializer(BaseReportWithPhotosSerializer):
    class IdentificationSerializer(serializers.ModelSerializer):
        photo = SimplePhotoSerializer(required=True)
        result = IdentificationTaskSerializer.IdentificationTaskResultSerializer(source='*', allow_null=True, read_only=True)

        class Meta:
            model = IdentificationTask
            fields = (
                'photo',
                'num_annotations',
                'result',
                'public_note'
            )
            extra_kwargs = {
                'num_annotations': {'source': 'total_finished_annotations', 'min_value': 0, 'read_only': True},
                'public_note': {'allow_null': True, 'allow_blank': True}
            }

    identification = IdentificationSerializer(source='identification_task', read_only=True, allow_null=True)

    class MosquitoAppearanceSerializer(serializers.ModelSerializer):
        def to_representation(self, instance):
            ret = super().to_representation(instance)

            if self.allow_null:
                if not any([instance.user_perceived_mosquito_specie,
                            instance.user_perceived_mosquito_thorax,
                            instance.user_perceived_mosquito_abdomen,
                            instance.user_perceived_mosquito_legs]):
                    return None

            return ret

        class Meta:
            model = Report
            fields = (
                "specie",
                "thorax",
                "abdomen",
                "legs"
            )
            extra_kwargs = {
                "specie": {"source": "user_perceived_mosquito_specie"},
                "thorax": {"source": "user_perceived_mosquito_thorax"},
                "abdomen": {"source": "user_perceived_mosquito_abdomen"},
                "legs": {"source": "user_perceived_mosquito_legs"},
            }

    mosquito_appearance = MosquitoAppearanceSerializer(
        source='*',
        required=False,
        allow_null=True,
        help_text="User-provided description of the mosquito's appearance"
    )

    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_ADULT
        return super().create(validated_data)

    class Meta(BaseReportWithPhotosSerializer.Meta):
        fields = BaseReportWithPhotosSerializer.Meta.fields + (
            "identification",
            "event_environment",
            "event_moment",
            "mosquito_appearance"
        )

class BiteSerializer(BaseReportSerializer):
    class BiteCountsSerializer(serializers.ModelSerializer):
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
            read_only_fields = ("total", )
            extra_kwargs = {
                "total": {"source": "bite_count"}
            }

    counts = BiteCountsSerializer(source='*')

    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_BITE
        return super().create(validated_data)

    class Meta(BaseReportSerializer.Meta):
        fields = BaseReportSerializer.Meta.fields + (
            "event_environment",
            "event_moment",
            "counts"
        )

class BreedingSiteSerializer(BaseReportWithPhotosSerializer):
    def create(self, validated_data):
        validated_data['type'] = Report.TYPE_SITE
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if not instance.breeding_site_type:
            ret['breeding_site_type'] = Report.BREEDING_SITE_TYPE_OTHER

        return ret

    class Meta(BaseReportWithPhotosSerializer.Meta):
        fields = BaseReportWithPhotosSerializer.Meta.fields + (
            "site_type",
            "has_water",
            "in_public_area",
            "has_near_mosquitoes",
            "has_larvae",
        )
        extra_kwargs = {
            "site_type": {"allow_null": False, "allow_blank": False, "source": "breeding_site_type"},
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
            "uuid": {"required": True},
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
class PhotoPredictionSerializer(serializers.ModelSerializer):
    class BoundingBoxSerializer(serializers.ModelSerializer):
        class Meta:
            model = PhotoPrediction
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
            model = PhotoPrediction
            fields = [fname.replace(PhotoPrediction.CLASS_FIELD_SUFFIX, '')  for fname in PhotoPrediction.get_score_fieldnames()]
            extra_kwargs = {
                fname.replace(PhotoPrediction.CLASS_FIELD_SUFFIX, ''): {"source": fname}
                for fname in PhotoPrediction.get_score_fieldnames()
            }

    photo = SimplePhotoSerializer(read_only=True)
    bbox = BoundingBoxSerializer(source='*')
    scores = PredictionScoreSerializer(source='*')

    class Meta:
        model = PhotoPrediction
        fields = (
            'photo',
            'bbox',
            'insect_confidence',
            'predicted_class',
            'threshold_deviation',
            'is_decisive',
            'scores',
            'classifier_version',
            'created_at',
            'updated_at'
        )
        extra_kwargs = {
            'predicted_class': {'required': True}
        }

class CreatePhotoPredictionSerializer(PhotoPredictionSerializer):
    photo_uuid = serializers.UUIDField(source='photo__uuid', required=True, write_only=True)

    def validate(self, data):
        data['identification_task_id'] = self.context.get('observation_uuid')
        photo__uuid = data.pop('photo__uuid')

        try:
            data['photo'] = Photo.objects.get(uuid=photo__uuid, report__identification_task=data['identification_task_id'])
        except Photo.DoesNotExist:
            raise serializers.ValidationError("The selected photo does not belong to this identification task or does not exist.")

        return data

    class Meta(PhotoPredictionSerializer.Meta):
        fields = ('photo_uuid',) + PhotoPredictionSerializer.Meta.fields