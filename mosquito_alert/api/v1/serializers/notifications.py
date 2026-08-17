from drf_spectacular.utils import extend_schema_field
import minify_html
from rest_framework import serializers

from mosquito_alert.api.v1.fields import HTMLCharField
from mosquito_alert.notifications.models import (
    NotificationContent,
    NotificationRecipient,
)
from mosquito_alert.users.models import TigaUser


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
