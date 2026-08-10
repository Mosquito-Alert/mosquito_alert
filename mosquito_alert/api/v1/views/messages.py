from drf_spectacular.utils import (
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response

from mosquito_alert.api.v1.filters import MessageFilter
from mosquito_alert.api.v1.permissions import MessagePermissions, MyMessagePermissions
from mosquito_alert.api.v1.serializers.messages import (
    CreateAudienceMessageSerializer,
    CreateMessageSerializer,
    CreateUserMessageSerializer,
    MessageListSerializer,
    MessageRecipientSerializer,
    MessageSerializer,
    MessageTargetingSerializer,
)
from mosquito_alert.api.v1.serializers.messages import MessageRecipientStatsSerializer
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.notifications.models import Notification, NotificationRecipient


@extend_schema_view(
    list=extend_schema(
        description="Get all messages sent by the current user. The content of the message is truncated to 100 words and the body is returned as plain text, without images or HTML tags. To retrieve the full content of a message, use the GET /messages/{id}/ endpoint.",
    ),
    create=extend_schema(
        request=PolymorphicProxySerializer(
            component_name="MetaCreateMessage",
            serializers={
                list(CreateUserMessageSerializer().fields["target"].choices.values())[
                    0
                ]: CreateUserMessageSerializer,
                list(
                    CreateAudienceMessageSerializer().fields["target"].choices.values()
                )[0]: CreateAudienceMessageSerializer,
            },
            resource_type_field_name="target",
        ),
        responses={201: OpenApiResponse(response=MessageSerializer)},
    ),
)
class MessageViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    filterset_class = MessageFilter
    permission_classes = (MessagePermissions,)
    serializer_class = MessageSerializer
    queryset = (
        Notification.objects.filter(expert__isnull=False)
        .select_related("notification_content", "expert")
        .all()
    )

    @property
    def pagination_class(self):
        if self.request.method == "POST":
            return None
        return super().pagination_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()

        response_serializer = MessageSerializer(notification)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_serializer_class(self):
        if self.action == "list":
            return MessageListSerializer
        if self.action == "create":
            target = self.request.data.get("target")
            user_target_value = list(
                CreateUserMessageSerializer().fields["target"].choices.values()
            )[0]
            audience_target_value = list(
                CreateAudienceMessageSerializer().fields["target"].choices.values()
            )[0]
            if target == user_target_value:
                return CreateUserMessageSerializer
            elif target == audience_target_value:
                return CreateAudienceMessageSerializer
            return CreateMessageSerializer

        return super().get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        if self.action == "recipients":
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)

    @action(
        detail=True,
        methods=["GET"],
        queryset=Notification.objects.select_related("expert").all(),
        serializer_class=MessageRecipientSerializer,
        filterset_class=(),
    )
    def recipients(self, request, *args, **kwargs):
        notification = self.get_object()

        recipients = NotificationRecipient.objects.filter(
            notification=notification
        ).select_related("user")

        page = self.paginate_queryset(recipients)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recipients, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["GET"],
        serializer_class=MessageRecipientStatsSerializer,
        url_path="recipients/stats",
    )
    def recipients_stats(self, request, *args, **kwargs):
        notification = self.get_object()

        stats = NotificationRecipient.objects.filter(notification=notification).stats()

        serializer = self.get_serializer(stats)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["GET"],
        serializer_class=MessageTargetingSerializer,
        filterset_class=(),
    )
    def targeting(self, request, *args, **kwargs):
        notification = self.get_object()

        serializer = self.get_serializer(notification)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["messages"],
        operation_id="messages_list_mine_sent",
        description="Get current user's sent messages",
    )
)
class MySentMessageViewSet(MessageViewSet):
    permission_classes = (MyMessagePermissions,)

    def get_queryset(self):
        return super().get_queryset().filter(expert=self.request.user)
