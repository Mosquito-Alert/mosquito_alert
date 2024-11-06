from django.contrib.auth import get_user_model
from django.db import models

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    PolymorphicProxySerializer,
)

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from tigaserver_app.models import (
    TigaUser,
    EuropeCountry,
    Notification,
    OrganizationPin,
    OWCampaigns,
    Report,
    Fix,
    Notification,
    Photo
)

from .filters import NotificationFilter, CampaignFilter, ObservationFilter, BiteFilter, BreedingSiteFilter
from .serializers import (
    PartnerSerializer,
    CampaignSerializer,
    UserSerializer,
    CreateUserSerializer,
    FixSerializer,
    CountrySerializer,
    PhotoSerializer,
    ObservationSerializer,
    BiteSerializer,
    BreedingSiteSerializer
)
from .serializers import (
    DetailNotificationSerializer,
    TopicNotificationCreateSerializer,
    UserNotificationCreateSerializer,
)
from .permissions import NotificationObjectPermissions, ReportPermissions
from .viewsets import GenericViewSet, GenericNoMobileViewSet

User = get_user_model()


class CampaignsViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = OWCampaigns.objects.all()
    serializer_class = CampaignSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = CampaignFilter


class CountriesViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = EuropeCountry.objects.all()
    serializer_class = CountrySerializer
    lookup_url_kwarg = "id"


class FixViewSet(CreateModelMixin, GenericViewSet):
    queryset = Fix.objects.all()
    serializer_class = FixSerializer


@extend_schema_view(
    create=extend_schema(
        request=PolymorphicProxySerializer(
            component_name="MetaNotification",
            serializers={
                "user": UserNotificationCreateSerializer,
                "topic": TopicNotificationCreateSerializer,
            },
            resource_type_field_name="receiver_type",
        ),
        responses=DetailNotificationSerializer
    )
)
class NotificationViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NotificationFilter

    permission_classes = (NotificationObjectPermissions,)

    queryset = (
        Notification.objects.select_related("notification_content")
        .prefetch_related("notification_acknowledgements")
        .all()
    )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()

        response_serializer = DetailNotificationSerializer(notification, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.request.method == "POST":
            notification_type = self.request.data.get("receiver_type")
            if notification_type == "user":
                return UserNotificationCreateSerializer
            elif notification_type == "topic":
                return TopicNotificationCreateSerializer
            else:
                raise ValidationError(
                    "Invalid 'receiver_type'. Must be 'user' or 'topic'"
                )
        return DetailNotificationSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user
        if isinstance(user, TigaUser):
            qs = qs.for_user(user=user)

        return qs


class PartnersViewSet(ReadOnlyModelViewSet, GenericViewSet):
    queryset = OrganizationPin.objects.all()
    serializer_class = PartnerSerializer


class BaseReportViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Report.objects.select_related('map_aux_report').prefetch_related(
        models.Prefetch(
            "photos",
            queryset=Photo.objects.visible()
        )
    ).non_deleted()

    lookup_url_kwarg = "uuid"

    filter_backends = (DjangoFilterBackend,)

    permission_classes = (ReportPermissions,)

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user
        if not isinstance(user, User):
            qs = qs.published()
            if isinstance(user, TigaUser):
                qs |= super().get_queryset().filter(user=user)

        return qs

    def perform_destroy(self, instance):
        instance.soft_delete()

class BaseReportWithPhotosViewSet(BaseReportViewSet):
    def get_parsers(self):
        # Since photos are required on POST, only allow
        # parasers that allow files.
        if self.request and self.request.method == 'POST':
            return [MultiPartParser(), FormParser()]
        return super().get_parsers()

class BiteViewSet(BaseReportViewSet):
    serializer_class = BiteSerializer
    filterset_class = BiteFilter

    def get_queryset(self):
        return super().get_queryset().filter(type=Report.TYPE_BITE)

class BreedingSiteViewSet(BaseReportWithPhotosViewSet):
    serializer_class = BreedingSiteSerializer
    filterset_class = BreedingSiteFilter

    def get_queryset(self):
        return super().get_queryset().filter(type=Report.TYPE_SITE)

class ObservationViewSest(BaseReportWithPhotosViewSet):
    serializer_class = ObservationSerializer
    filterset_class = ObservationFilter

    def get_queryset(self):
        return super().get_queryset().filter(type=Report.TYPE_ADULT)


class UserViewSet(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet
):
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer

    lookup_url_kwarg = "uuid"

    def get_permissions(self):
        if self.request and self.request.method == "POST":
            return [AllowAny(),]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateUserSerializer
        else:
            return UserSerializer

class PhotoViewSet(
    RetrieveModelMixin, GenericNoMobileViewSet
):
    queryset = Photo.objects.visible()
    serializer_class = PhotoSerializer

    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'
