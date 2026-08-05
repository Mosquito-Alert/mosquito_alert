from rest_framework import serializers

from mosquito_alert.api.v1.serializers.photos import SimplePhotoSerializer
from mosquito_alert.api.v1.serializers.taxa import SimpleTaxonSerializer
from mosquito_alert.identification_tasks.models import PhotoPrediction
from mosquito_alert.reports.models import Photo


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
