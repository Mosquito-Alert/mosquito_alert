from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from tigaserver_app.models import (
    TigaUser,
    UserSubscription,
    NotificationContent,
    Notification,
    OrganizationPin,
    OWCampaigns,
    Report,
    Session,
    Photo,
    Fix,
    ReportResponse,
    Notification,
)

from .serializers import (
    NotificationContentSerializer,
    NotificationSerializer,
    UserSubscriptionSerializer,
    OrganizationPinSerializer,
    OWCampaignsSerializer,
    UserSerializer,
    ReportListSerializer,
    ReportDetailSerializer,
    SessionSerializer,
    PhotoSerializer,
    FixSerializer,
    ReportResponseSerializer,
)

# TODO: notifications can we sent to either to a user or to a topic.


class NotificationContentView(CreateModelMixin, GenericViewSet):
    queryset = NotificationContent.objects.all()
    serializer_class = NotificationContentSerializer

    # TODO: only users with permissions to create notifications
    # permission_classes = []


class NotificationView(CreateModelMixin, GenericViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    # TODO: mark notification as ack (Create AcknowledgedNotification(user=u, notification=n))

    def create(self, request, *args, **kwargs):
        # OPTIONS:
        # notification_content_id, user_id (sender), ppush, report_id, recipientd

        # Only allow topic_code or user_ids

        # I would make:
        # notification_content_id
        # report_id
        # user_id (received)
        # topic_code
        # push

        notify_all = request.query_params.get("notify_all", "").lower() == "true"

        if notify_all:
            # Check if the user has the specific permission to enable notify_all
            self.check_object_permissions(request, None)
            return self.create_bulk_notification(request)
        else:
            return super().create(request, *args, **kwargs)

    def create_bulk_notification(self, request):
        users = (
            TigaUser.objects.exclude(device_token="")
            .filter(device_token__isnull=False)
            .all()
        )
        notifications = []

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for user in users:
            notification = serializer.save(predefined_available_to=user)
            notifications.append(notification)

        serializer = self.get_serializer(notifications, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        # Set the user field to the current user when creating a new record
        serializer.save(expert_id=self.request.user)


class UserSubscriptionView(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow users to modify their own records
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the user field to the current user when creating a new record
        serializer.save(user=self.request.user)


class OrganizationPinViewSet(ReadOnlyModelViewSet):
    queryset = OrganizationPin.objects.order_by("pk").all()
    serializer_class = OrganizationPinSerializer
    filter_backends = [filters.OrderingFilter]
    ordering = [
        "id",
    ]


class OWCampaignsViewSet(ReadOnlyModelViewSet):
    queryset = OWCampaigns.objects.select_related("country").all()
    serializer_class = OWCampaignsSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        "country",
    ]
    ordering = [
        "campaign_start_date",
    ]


class UserViewSet(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet
):
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: SessionSerializer(many=True)},
    )
    @swagger_auto_schema(
        method="post",
        request_body=SessionSerializer,
        responses={201: SessionSerializer()},
    )
    @swagger_auto_schema(
        method="put",
        request_body=SessionSerializer,
        responses={200: SessionSerializer()},
    )
    @action(detail=True, methods=["get", "post", "put"])
    def sessions(self, request, pk=None):
        user = self.get_object()

        if request.method == "GET":
            sessions = Session.objects.filter(user=user).order_by("session_start_time")
            serializer = SessionSerializer(sessions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "POST":
            # Handle POST request to create a new session
            serializer = SessionSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == "PUT":
            # Assuming you provide the session ID in the URL as 'api/users/<user_id>/sessions/<session_id>/'
            session = Session.objects.get(pk=pk)

            serializer = SessionSerializer(instance=session, data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: NotificationSerializer(many=True)},
    )
    @action(methods=["get"], detail=True)
    def notifications(self, request, pk=None):
        user = self.get_object()
        acknowledged = self.request.data.get("acknowledged", None)

        # Filters: locale, user_id, acknowledged
        notifications_qs = Notification.objects.filter(
            Q(notification_sendings__sent_to_user=user)
            | Q(notification_sendings__sent_to_topic__topic_code="global")
            | Q(notification_sendings__sent_to_topic__topic_users__user=user)
        )

        if acknowledged is not None:
            filter_args = Q(notification_acknowledgements__user=user)
            if not acknowledged:
                filter_args = ~filter_args

            notifications_qs = notifications_qs.filter(filter_args)

        notifications_qs = notifications_qs.order_by("-date_comment")

        serializer = NotificationSerializer(notifications_qs.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        # Check if the client provided a custom UUID
        provided_uuid = self.request.data.get("user_UUID")

        if provided_uuid:
            # Use the provided UUID
            serializer.save(user_UUID=provided_uuid)
        else:
            # Let DRF generate a new UUID
            serializer.save()


class ReportViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    queryset = Report.objects.all()

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["server_upload_time", "creation_time"]
    ordering = [
        "server_upload_time",
    ]
    filterset_fields = (
        "user",
        "version_number",
        "report_id",
        "type",
        "server_upload_time",
        "creation_time",
        "country",
        "nuts_3",
        "nuts_2",
    )

    def get_serializer_class(self):
        if self.action == "list":
            return ReportListSerializer
        return ReportDetailSerializer

    def perform_create(self, serializer):
        # Set the user field to the current user when creating a new record
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: PhotoSerializer(many=True)},
    )
    @swagger_auto_schema(
        method="post",
        request_body=PhotoSerializer,
        responses={201: PhotoSerializer()},
    )
    @action(detail=True, methods=["get", "post"])
    def photos(self, request, pk=None):
        report = self.get_object()

        if request.method == "GET":
            photos = Photo.objects.filter(report=report)
            serializer = PhotoSerializer(photos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == "POST":
            # Handle POST request to create a new session
            serializer = PhotoSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save(report=report)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: ReportResponseSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def responses(self, request, pk=None):
        report = self.get_object()
        responses = ReportResponse.objects.filter(report=report)
        serializer = ReportResponseSerializer(responses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionViewSet(CreateModelMixin, GenericViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    # def get_queryset(self):
    #     # Only allow users to modify their own records
    #     return super().get_queryset().filter(user=self.request.user)


class PhotoViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("report", "uuid")

    def get_queryset(self):
        # Only allow users to modify their own records
        return super().get_queryset().filter(report__user=self.request.user)


class FixViewSet(CreateModelMixin, GenericViewSet):
    queryset = Fix.objects.all()
    serializer_class = FixSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ("user_coverage_uuid", "fix_time", "server_upload_time")
