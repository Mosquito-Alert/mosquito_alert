from rest_framework import serializers

from mosquito_alert.reports.models import Photo


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
