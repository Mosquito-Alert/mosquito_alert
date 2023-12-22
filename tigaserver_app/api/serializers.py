import json
from rest_framework import serializers


from tigaserver_app.models import (
    NotificationContent,
    Notification,
    UserSubscription,
    OrganizationPin,
    OWCampaigns,
    EuropeCountry,
    TigaUser,
    Report,
    ReportResponse,
    Session,
    Photo,
    Fix,
)


class NotificationContentSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        # Ensure that body_html_en and title_en are provided
        if not attrs.get("body_html_en"):
            raise serializers.ValidationError(
                {"body_html_en": "This field is required."}
            )
        if not attrs.get("title_en"):
            raise serializers.ValidationError({"title_en": "This field is required."})

        return super().validate(attrs=attrs)

    class Meta:
        model = NotificationContent
        fields = (
            "body_html_en",
            "body_html_native",
            "title_en",
            "title_native",
            "native_locale",
            "notification_label",
        )


class NotificationSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if not attrs.get("notification_content_id"):
            raise serializers.ValidationError(
                {"notification_content_id": "This field is required."}
            )

        return super().validate(attrs=attrs)

    class Meta:
        model = Notification
        fields = (
            "id",
            "report",
            # "user",
            "expert",
            "date_comment",
            "notification_content",
            "expert_comment",
            "expert_html",
            "photo_url",
            "public",
            "acknowledged",
        )


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = "__all__"
        read_only_fields = ("user",)


class OrganizationPinSerializer(serializers.ModelSerializer):
    point = serializers.SerializerMethodField(method_name="get_point")

    class Meta:
        model = OrganizationPin
        fields = "__all__"

    def get_point(self, obj):
        if obj.point is not None:
            return {"lat": obj.point.y, "long": obj.point.x}
        else:
            return None


class EuropeCountrySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EuropeCountry
        fields = ("gid", "name_engl")


class OWCampaignsSerializer(serializers.ModelSerializer):
    country = EuropeCountrySimpleSerializer()

    class Meta:
        model = OWCampaigns
        fields = "__all__"


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TigaUser
        fields = (
            "user_UUID",
            "registration_time",
            "device_token",
            "score_v2",
            "score_v2_struct",
            "last_score_update",
        )
        read_only_fields = (
            "registration_time",
            "score_v2",
            "score_v2_struct",
            "last_score_update",
        )
        extra_kwargs = {
            "device_token": {"write_only": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data["score_v2_struct"] = json.loads(data["score_v2_struct"])
        except Exception:
            pass
        return data


class ReportResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportResponse
        fields = ["question_id", "question", "answer_id", "answer", "answer_value"]


class ReportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"


class ReportDetailSerializer(serializers.ModelSerializer):
    responses = ReportResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = "__all__"


class PhotoSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ("photo", "report", "uuid")
        read_only_fields = ("uuid",)
        extra_kwargs = {
            "report": {"write_only": True},
        }

    def get_photo(self, obj):
        # TODO: change this
        statics_domain = "https://your-api-domain.com"  # Replace with your API domain
        image_url = obj.photo.url
        return f"{statics_domain}{image_url}"


class FixSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        # Ensure that user_coverage_uuid
        if not attrs.get("user_coverage_uuid"):
            raise serializers.ValidationError(
                {"user_coverage_uuid": "This field is required."}
            )

        return super().validate(attrs=attrs)

    class Meta:
        model = Fix
        fields = "__all__"
        read_only_fields = ("server_upload_time",)
