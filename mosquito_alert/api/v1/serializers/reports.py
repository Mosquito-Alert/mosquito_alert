# TODO: Move the Identification Task related serializers to the identification_tasks.py file. Problem: Circular imports.
from datetime import datetime
from typing import Literal, Optional

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone

from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers

from rest_framework_csv.renderers import CSVStreamingRenderer
from rest_framework_gis.serializers import GeoFeatureModelSerializer
import rules
from taggit.serializers import TaggitSerializer, TagListSerializerField

from mosquito_alert.api.v1.serializers.photos import SimplePhotoSerializer
from mosquito_alert.api.v1.serializers.taxa import SimpleTaxonSerializer
from mosquito_alert.api.v1.serializers.users import (
    SimpleUserSerializer,
    MinimalUserSerializer,
)

from .countries import CountrySerializer
from mosquito_alert.geo.models import (
    LauEurope,
    NutsEurope,
)
from mosquito_alert.identification_tasks.models import (
    IdentificationTask,
    ExpertReportAnnotation,
)
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.users.models import UserStat


from ..fields import (
    TimezoneAwareDateTimeField,
    WritableSerializerMethodField,
    IntegerDefaultField,
    TimeZoneSerializerChoiceField,
)
from ..mixins import ReportGeoJsonModelSerializerMixin

User = get_user_model()


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
    user = MinimalUserSerializer(read_only=True)
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
            "user",
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


class SimplifiedObservationSerializer(BaseSimplifiedReportSerializer):
    class Meta(BaseSimplifiedReportSerializer.Meta):
        pass


class SimplifiedObservationWithPhotosSerializer(
    BaseSimplifiedReportSerializerWithPhoto
):
    class Meta(BaseSimplifiedReportSerializerWithPhoto.Meta):
        pass


# Identification Task serializer
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


# Identification Task serializer
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


# Identification Task serializer
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

        can_set_is_executive = rules.test_rule(
            "can_set_executive_annotation", data["user"], data["identification_task"]
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


# Identification Task serializer
class BaseAssignmentSerializer(serializers.ModelSerializer):
    annotation_type = serializers.SerializerMethodField()

    def get_annotation_type(self, obj) -> Literal["short", "long"]:
        return "short" if obj.is_simplified else "long"

    class Meta:
        model = ExpertReportAnnotation
        fields = ("annotation_type",)


# Identification Task serializer
class AssignmentSerializer(BaseAssignmentSerializer):
    observation = serializers.SerializerMethodField()

    @extend_schema_field(SimplifiedObservationWithPhotosSerializer)
    def get_observation(self, obj: ExpertReportAnnotation) -> dict:
        serializer = SimplifiedObservationWithPhotosSerializer(
            obj.identification_task.report,
            context={
                **self.context,
                "hide_note_if_not_owner": False,
            },  # always show note
        )
        return serializer.data

    class Meta(BaseAssignmentSerializer.Meta):
        fields = ("observation",) + BaseAssignmentSerializer.Meta.fields


# Identification Task serializer
class IdentificationTaskSerializer(serializers.ModelSerializer):
    class IdentificationTaskCapabilitiesSerializer(serializers.ModelSerializer):
        review = serializers.SerializerMethodField()
        annotate = serializers.SerializerMethodField()
        annotate_executive = serializers.SerializerMethodField()

        def get_review(self, obj: IdentificationTask) -> bool:
            user = self.context["request"].user

            return user.has_perm(
                f"{IdentificationTask._meta.app_label}.add_review", obj
            )

        def get_annotate(self, obj: IdentificationTask) -> bool:
            user = self.context["request"].user

            return user.has_perm(
                "%(app_label)s.add_%(model_name)s"
                % {
                    "app_label": ExpertReportAnnotation._meta.app_label,
                    "model_name": ExpertReportAnnotation._meta.model_name,
                },
                obj,
            )

        def get_annotate_executive(self, obj: IdentificationTask) -> bool:
            user = self.context["request"].user
            return rules.test_rule("can_set_executive_annotation", user, obj)

        class Meta:
            model = IdentificationTask
            fields = ("review", "annotate", "annotate_executive")

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


# Identification Task serializer
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


# Identification Task serializer
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


# Identification Task serializer
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
