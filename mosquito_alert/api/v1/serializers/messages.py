from django.db import transaction
from rest_framework import serializers

from mosquito_alert.notifications.utils import truncate_html_to_words

from .base_serializers import LocalizedModelSerializerMixin
from .users import AudienceFilterSerializer, MinimalUserSerializer, SimpleUserSerializer
from mosquito_alert.notifications.models import (
    Notification,
    NotificationContent,
    NotificationRecipient,
)
from mosquito_alert.users.models import TigaUser
from mosquito_alert.workspaces.models import Workspace, WorkspaceCollaborationGroup


# * ############### DETAIL SERIALIZERS ###############
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


class MessageContentSerializer(serializers.ModelSerializer):
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


class MessageSerializer(serializers.ModelSerializer):
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

    target = serializers.SerializerMethodField()

    def get_target(self, obj: Notification) -> Notification.Target:
        return obj.target

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
            "target",
            "created_at",
        )


# * ############### LIST SERIALIZERS ###############
class LocalizedMessageBodyPreviewSerializer(LocalizedMessageBodySerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)

        return {
            language: truncate_html_to_words(value, 100) if value else value
            for language, value in data.items()
        }


class MessageListContentSerializer(MessageContentSerializer):
    body = LocalizedMessageBodyPreviewSerializer(
        source="*.body_html",
        is_html=True,
        help_text="Provide the message's body in all supported languages",
    )


class MessageListSerializer(MessageSerializer):
    content = MessageListContentSerializer(
        source="notification_content",
        read_only=True,
    )


# * ############### CREATE SERIALIZERS ###############


class CreateMessageSerializer(MessageSerializer):
    # The "target" field is a hidden field that is automatically populated with the value of "target" from the request context. This allows the serializer to determine the target audience for the message without requiring the client to explicitly provide it in the request data.
    target = serializers.HiddenField(
        default=lambda field: field.context["request"].target, source="*"
    )

    def validate_target(self, value):
        return {}

    class Meta(MessageSerializer.Meta):
        pass


class CreateUserMessageSerializer(CreateMessageSerializer):
    target = serializers.ChoiceField(
        source="*", choices=[Notification.Target.USERS.value]
    )
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

    class Meta(CreateMessageSerializer.Meta):
        fields = CreateMessageSerializer.Meta.fields + ("user_uuids",)


class CreateAudienceMessageSerializer(CreateMessageSerializer):
    class CreateAudienceMessageContentSerializer(serializers.ModelSerializer):
        class LocalizedAudienceMessageTitleSerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        class LocalizedAudienceMessageBodySerializer(
            LocalizedModelSerializerMixin, serializers.ModelSerializer
        ):
            class Meta:
                model = NotificationContent

        title = LocalizedAudienceMessageTitleSerializer(
            source="*.title",
            required_languages=[
                "en"
            ],  # For audience messages, english is required as fallback if user locale is not supported.
            max_length=255,
            help_text="Provide the message's title in all supported languages for this audience",
        )
        body = LocalizedAudienceMessageBodySerializer(
            source="*.body_html",
            required_languages=[
                "en"
            ],  # For audience messages, english is required as fallback if user locale is not supported.
            help_text="Provide the message's body in all supported languages for this audience",
        )

        class Meta:
            model = NotificationContent
            fields = ("title", "body")

    target = serializers.ChoiceField(
        source="*", choices=[Notification.Target.AUDIENCE.value]
    )

    content = CreateAudienceMessageContentSerializer(
        source="notification_content",
        required=True,
        help_text="The content of the message for the audience",
    )

    audience = AudienceFilterSerializer(
        required=True, help_text="The audience filter for the message"
    )

    def _get_workspace_coverage_geometry(self, workspace: Workspace):
        if workspace.geom is not None:
            return workspace.geom

        if workspace.country is not None and workspace.country.geom is not None:
            return workspace.country.geom

        return None

    def _is_audience_geometry_allowed_for_user(
        self, *, user, audience_geometry
    ) -> bool:
        collaboration_groups = WorkspaceCollaborationGroup.objects.filter(
            reviewers=user
        ).prefetch_related("workspaces__country")

        for collaboration_group in collaboration_groups:
            collaboration_group_geometry = None
            for workspace in collaboration_group.workspaces.all():
                workspace_geometry = self._get_workspace_coverage_geometry(
                    workspace=workspace
                )
                if workspace_geometry is None:
                    continue

                if collaboration_group_geometry is None:
                    collaboration_group_geometry = workspace_geometry
                else:
                    collaboration_group_geometry = collaboration_group_geometry.union(
                        workspace_geometry
                    )

            if (
                collaboration_group_geometry is not None
                and collaboration_group_geometry.covers(audience_geometry)
            ):
                return True

        return False

    def validate_audience(self, value):
        print("value", value)
        audience_geometry = value.get("last_location__within")
        if audience_geometry is None:
            return value

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError(
                "Authenticated user is required to validate audience geometry."
            )

        if not self._is_audience_geometry_allowed_for_user(
            user=user,
            audience_geometry=audience_geometry,
        ):
            raise serializers.ValidationError(
                "Audience geometry is outside the scope of your workspace collaboration groups."
            )

        return value

    class Meta(CreateMessageSerializer.Meta):
        fields = CreateMessageSerializer.Meta.fields + ("audience",)


class MessageTargetingSerializer(serializers.ModelSerializer):
    target = MessageSerializer().fields["target"]
    audience = AudienceFilterSerializer(required=False, allow_null=True)

    def get_target(self, obj: Notification) -> Notification.Target:
        return obj.target

    class Meta:
        model = Notification
        fields = ("target", "audience")


class MessageRecipientSerializer(serializers.ModelSerializer):
    user = MinimalUserSerializer(read_only=True)
    has_read = serializers.BooleanField(source="is_read", read_only=True)

    class Meta:
        model = NotificationRecipient
        fields = ("user", "has_read")


class MessageRecipientStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    read = serializers.IntegerField()
    unread = serializers.IntegerField()
