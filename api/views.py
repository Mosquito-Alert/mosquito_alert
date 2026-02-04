from typing import Optional
import uuid

from django.contrib.auth import get_user_model
from django.db import models

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    PolymorphicProxySerializer,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes
)

from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.parsers import FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_simplejwt.tokens import Token

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation, Taxon, PhotoPrediction, FavoritedReports, UserStat
from tigaserver_app.models import (
    TigaUser,
    EuropeCountry,
    Notification,
    OrganizationPin,
    OWCampaigns,
    Report,
    Fix,
    Notification,
    Photo,
    Device
)

from .filters import (
    NotificationFilter,
    CampaignFilter,
    ObservationFilter,
    BiteFilter,
    BreedingSiteFilter,
    IdentificationTaskFilter,
    AnnotationFilter,
    TaxonFilter
)
from .mixins import IdentificationTaskNestedAttribute
from .parsers import MultiPartJsonNestedParser
from .serializers import (
    PartnerSerializer,
    CampaignSerializer,
    UserSerializer,
    FixSerializer,
    CountrySerializer,
    PhotoSerializer,
    SimplePhotoSerializer,
    ObservationSerializer,
    BiteSerializer,
    BreedingSiteSerializer,
    DeviceSerializer,
    DeviceUpdateSerializer,
    AnnotationSerializer,
    AssignmentSerializer,
    IdentificationTaskSerializer,
    TaxonSerializer,
    TaxonTreeNodeSerializer,
    PhotoPredictionSerializer,
    CreatePhotoPredictionSerializer,
    UserPermissionSerializer,
    CreateAgreeReviewSerializer,
    CreateOverwriteReviewSerializer
)
from .serializers import (
    CreateNotificationSerializer,
    NotificationSerializer,
    TopicNotificationCreateSerializer,
    UserNotificationCreateSerializer,
)
from .permissions import (
    UserRolePermission,
    UserPermissions,
    NotificationObjectPermissions,
    MyNotificationPermissions,
    ReportPermissions,
    MyReportPermissions,
    IdentificationTaskPermissions,
    MyIdentificationTaskPermissions,
    IdentificationTaskAssignmentPermissions,
    IdentificationTaskReviewPermissions,
    AnnotationPermissions,
    MyAnnotationPermissions,
    PhotoPredictionPermissions,
    TaxaPermissions,
    CountriesPermissions
)
from .viewsets import GenericViewSet, GenericMobileOnlyViewSet, GenericNoMobileViewSet, NestedViewSetMixin

User = get_user_model()

@extend_schema(
    responses={204: None},  # No content
    description="Simple ping endpoint to check API connectivity"
)
@api_view(['GET'])
@authentication_classes([])  # no auth
@permission_classes([])      # no permissions
def ping(request):
    return Response(status=status.HTTP_204_NO_CONTENT)

class CampaignsViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = OWCampaigns.objects.all()
    serializer_class = CampaignSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = CampaignFilter


class CountriesViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = EuropeCountry.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (CountriesPermissions,)

    lookup_url_kwarg = "id"


class FixViewSet(CreateModelMixin, GenericViewSet):
    queryset = Fix.objects.all()
    serializer_class = FixSerializer


@extend_schema_view(
    create=extend_schema(
        request=PolymorphicProxySerializer(
            component_name="MetaNotification",
            serializers={
                UserNotificationCreateSerializer().fields['receiver_type'].get_default(): UserNotificationCreateSerializer,
                TopicNotificationCreateSerializer().fields['receiver_type'].get_default(): TopicNotificationCreateSerializer,
            },
            resource_type_field_name="receiver_type",
        ),
        responses={
            201: OpenApiResponse(
                response=CreateNotificationSerializer(many=True)
            )
        }
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

    @property
    def pagination_class(self):
        if self.request.method == "POST":
            return None
        return super().pagination_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notifications = serializer.save()

        response_serializer = CreateNotificationSerializer(notifications, context=self.get_serializer_context(), many=True)
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
        return NotificationSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user
        if isinstance(user, TigaUser):
            qs = qs.for_user(user=user)

        return qs

@extend_schema_view(
    list=extend_schema(
        tags=['notifications'],
        operation_id='notifications_list_mine',
        description="Get Current User's Notifications"
    )
)
class MyNotificationViewSet(NotificationViewSet, GenericMobileOnlyViewSet):
    permission_classes = (MyNotificationPermissions,)
    def get_queryset(self):
        return super().get_queryset().for_user(user=self.request.user)

class PartnersViewSet(ReadOnlyModelViewSet, GenericViewSet):
    queryset = OrganizationPin.objects.all()
    serializer_class = PartnerSerializer


# NOTE: this can be removed if Report.version_UUID is ever changed to UUIDField (from CharField)
REPORT_VIEW_LOOKUP_FIELD = "uuid"
REPORT_UUID_PATH_PARAM = OpenApiParameter(
    name=REPORT_VIEW_LOOKUP_FIELD,
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
)
@extend_schema_view(
    retrieve=extend_schema(parameters=[REPORT_UUID_PATH_PARAM]),
    destroy=extend_schema(parameters=[REPORT_UUID_PATH_PARAM]),
    update=extend_schema(parameters=[REPORT_UUID_PATH_PARAM]),
    partial_update=extend_schema(parameters=[REPORT_UUID_PATH_PARAM]),
)
class BaseReportViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    queryset = Report.objects.select_related(
        "nuts_2_fk",
        "nuts_3_fk",
        "lau_fk",
        "country",
        "identification_task",
        "identification_task__photo",
        "identification_task__taxon",
    ).prefetch_related(
        'tags',
        models.Prefetch(
            "photos",
            queryset=Photo.objects.visible()
        )
    ).annotate(
        pk_str=models.functions.Cast('pk', output_field=models.CharField()),
    ).non_deleted().filter(point__isnull=False).order_by('-server_upload_time')

    lookup_url_kwarg = REPORT_VIEW_LOOKUP_FIELD

    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("report_id", "pk_str")

    permission_classes = (ReportPermissions,)

    def get_permissions(self):
        # Check if the request is for an action
        if self.action and hasattr(self, self.action):
            action_method = getattr(self, self.action)
            if action_method and hasattr(action_method, 'kwargs'):
                action_permissions = action_method.kwargs.get('permission_classes')
                if action_permissions:
                    return [permission() for permission in action_permissions]

        if self.request and self.request.method in SAFE_METHODS:
            return [AllowAny(),]

        return super().get_permissions()

    def get_serializer_context(self, *args, **kwargs):
        result = super().get_serializer_context(*args, **kwargs)
        if self.request.user.is_authenticated and isinstance(self.request.user, User):
            # If user has view permissions, never hide.
            result['hide_note_if_not_owner'] = not self.request.user.has_perm(
                f"{Report._meta.app_label}.view_{Report._meta.model_name}"
            )

        return result

    def _get_device_from_jwt(self) -> Optional[Device]:
        if not self.request:
            return

        if not isinstance(self.request.auth, Token):
            return

        device_id = self.request.auth.get('device_id')
        if not device_id:
            return

        try:
            return Device.objects.get(
                user=self.request.user,
                device_id=device_id
            )
        except Device.DoesNotExist:
            return

    def perform_create(self, serializer):
        kwargs = {}
        user = self.request.user
        if isinstance(user, TigaUser):
            kwargs['app_language'] = user.locale

        device = self._get_device_from_jwt()
        if device:
            kwargs['device'] = device
            kwargs['device_manufacturer'] = device.manufacturer
            kwargs['device_model'] = device.model
            kwargs['os'] = device.os_name
            kwargs['os_version'] = device.os_version
            kwargs['os_language'] = device.os_locale
            if device.mobile_app:
                kwargs['mobile_app'] = device.mobile_app
                kwargs['package_name'] = device.mobile_app.package_name
                v = device.mobile_app.package_version
                kwargs['package_version'] = int(f"{v.major}{v.minor:02d}")
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        self.perform_create(serializer=serializer)

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

class BaseMyReportViewSet(BaseReportViewSet, GenericMobileOnlyViewSet):
    def get_permissions(self):
        return [MyReportPermissions(),]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class BaseReportWithPhotosViewSet(BaseReportViewSet):
    def get_parsers(self):
        # Since photos are required on POST, only allow
        # parasers that allow files.
        if self.request and self.request.method == 'POST':
            return [MultiPartJsonNestedParser(), FormParser()]
        return super().get_parsers()

class BiteViewSet(BaseReportViewSet):
    serializer_class = BiteSerializer
    filterset_class = BiteFilter

    queryset = BaseReportWithPhotosViewSet.queryset.filter(type=Report.TYPE_BITE)

@extend_schema_view(
    list=extend_schema(
        tags=['bites'],
        operation_id='bites_list_mine',
        description="Get Current User's Bites"
    )
)
class MyBiteViewSet(BaseMyReportViewSet, BiteViewSet):
    pass

class BreedingSiteViewSet(BaseReportWithPhotosViewSet):
    serializer_class = BreedingSiteSerializer
    filterset_class = BreedingSiteFilter

    queryset = BaseReportWithPhotosViewSet.queryset.filter(type=Report.TYPE_SITE)

@extend_schema_view(
    list=extend_schema(
        tags=['breeding-sites'],
        operation_id='breedingsites_list_mine',
        description="Get Current User's Breeding Sites"
    )
)
class MyBreedingSiteViewSet(BaseMyReportViewSet, BreedingSiteViewSet):
    pass

class ObservationViewSest(BaseReportWithPhotosViewSet):
    serializer_class = ObservationSerializer
    filterset_class = ObservationFilter

    queryset = BaseReportWithPhotosViewSet.queryset.filter(type=Report.TYPE_ADULT)


@extend_schema_view(
    list=extend_schema(
        tags=['observations'],
        operation_id='observations_list_mine',
        description="Get Current User's Observations"
    )
)
class MyObservationViewSest(BaseMyReportViewSet, ObservationViewSest):
    pass

# NOTE: this can be removed if TigaUser.user_UUID is ever changed to UUIDField (from CharField)
USER_VIEW_LOOKUP_FIELD = "uuid"
USER_UUID_PATH_PARAM = OpenApiParameter(
    name=USER_VIEW_LOOKUP_FIELD,
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
)
@extend_schema_view(
    retrieve=extend_schema(parameters=[USER_UUID_PATH_PARAM]),
    destroy=extend_schema(parameters=[USER_UUID_PATH_PARAM]),
    update=extend_schema(parameters=[USER_UUID_PATH_PARAM]),
    partial_update=extend_schema(parameters=[USER_UUID_PATH_PARAM]),
)
class UserViewSet(
    UpdateModelMixin, RetrieveModelMixin, GenericViewSet
):
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer

    permission_classes = (UserPermissions,)

    lookup_url_kwarg = USER_VIEW_LOOKUP_FIELD

    def get_object(self):
        try:
            # Perform the lookup filtering.
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            obj = User.objects.get(pk=uuid.UUID(self.kwargs[lookup_url_kwarg]).int)
            self.check_object_permissions(self.request, obj)
            return obj
        except User.DoesNotExist:
            return super().get_object()

    def update(self, request, *args, **kwargs):
        if isinstance(self.get_object(), User):
            self.permission_denied(request)
        return super().update(request, *args, **kwargs)


@extend_schema_view(
    retrieve=extend_schema(
        tags=['users'],
        operation_id='users_retrieve_mine',
        description="Get Current User's Profile"
    )
)
class MyUserViewSet(UserViewSet):
    # NOTE: do not remove this retrieve, it is needed in order to no inherit extend_schema_view from
    #       parent class, which forces a uuid paramenter in the path.
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_object(self):
        user = self.request.user
        # May raise a permission denied
        self.check_object_permissions(self.request, user)

        return user

@extend_schema_view(
    retrieve=extend_schema(
        tags=['permissions'],
        operation_id='permissions_retrieve_mine',
        description="Get Current User's Permissions"
    )
)
class MyPermissionViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = None
    serializer_class = UserPermissionSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        # May raise a permission denied
        self.check_object_permissions(self.request, user)

        return user

class PhotoViewSet(
    RetrieveModelMixin, GenericNoMobileViewSet
):
    queryset = Photo.objects.visible()
    serializer_class = PhotoSerializer

    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    @action(
        detail=True,
        methods=['GET', 'PUT', 'PATCH', 'DELETE'],
        authentication_classes=GenericNoMobileViewSet.authentication_classes,
        permission_classes=GenericNoMobileViewSet.permission_classes,
        parser_classes=GenericViewSet.parser_classes,
        serializer_class=PhotoPredictionSerializer,
        queryset=PhotoPrediction.objects.all().select_related("taxon"),
        lookup_field='photo__uuid',
        filter_backends=[]
    )
    def prediction(self, request, uuid=None):
        if request.method == 'GET':
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.context['photo__uuid'] = uuid
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self._get_location_header(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == 'DELETE':
            instance = self.get_object()
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _get_location_header(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

class DeviceViewSet(CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericMobileOnlyViewSet):
    queryset = Device.objects.filter(device_id__isnull=False).exclude(device_id='').select_related('mobile_app')
    serializer_class = DeviceSerializer

    lookup_field = 'device_id'
    lookup_url_kwarg = 'device_id'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DeviceUpdateSerializer
        else:
            return DeviceSerializer


# NOTE: this can be removed if Report.version_UUID is ever changed to UUIDField (from CharField)
IDENTIFICATION_TASK_VIEW_LOOKUP_FIELD = "observation_uuid"
OBSERVATION_UUID_PATH_PARAM = OpenApiParameter(
    name=IDENTIFICATION_TASK_VIEW_LOOKUP_FIELD,
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
)
@extend_schema_view(
    retrieve=extend_schema(parameters=[OBSERVATION_UUID_PATH_PARAM]),
    destroy=extend_schema(parameters=[OBSERVATION_UUID_PATH_PARAM]),
    update=extend_schema(parameters=[OBSERVATION_UUID_PATH_PARAM]),
    partial_update=extend_schema(parameters=[OBSERVATION_UUID_PATH_PARAM]),
    review=extend_schema(parameters=[OBSERVATION_UUID_PATH_PARAM]),
)
class IdentificationTaskViewSet(RetrieveModelMixin, ListModelMixin, GenericNoMobileViewSet):
    queryset = IdentificationTask.objects.all().select_related(
        'taxon',
        'photo',
        'report',
        'report__country',
        # NOTE: needed for get_display_name
        'report__nuts_2_fk',
        'report__nuts_3_fk',
        'report__lau_fk'
    ).prefetch_related(
        models.Prefetch(
            "assignees",
            queryset=User.objects.filter(
                models.Exists(
                    ExpertReportAnnotation.objects.is_assignment().filter(
                        user=models.OuterRef('pk'),
                        identification_task_id=models.OuterRef(models.OuterRef('identificationtask'))
                    )
                )
            )
        ),
        models.Prefetch(
            "report__photos",
            queryset=Photo.objects.visible(),
        )
    ).annotate(
        pk_str=models.functions.Cast('pk', output_field=models.CharField()),
    )
    serializer_class = IdentificationTaskSerializer
    filterset_class = IdentificationTaskFilter
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("report__report_id", "pk_str")
    permission_classes = (IdentificationTaskPermissions | UserRolePermission,)

    lookup_field = 'pk'
    lookup_url_kwarg = IDENTIFICATION_TASK_VIEW_LOOKUP_FIELD

    def get_queryset(self):
        return super().get_queryset().browsable(user=self.request.user)

    @extend_schema(
        request=None,
        responses={
            201: AssignmentSerializer,
            204: OpenApiResponse(description="No available tasks pending to assign"),
        },
        operation_id='identificationtasks_assign_next',
        description="Assign the next available identification task.",
    )
    @action(detail=False, methods=["POST",], url_path="assignments/next", permission_classes=[IdentificationTaskAssignmentPermissions,], serializer_class=AssignmentSerializer)
    def assign_next(self, request):
        # Checking if there are any assignments with pending annotation for that user.
        assignment = ExpertReportAnnotation.objects.is_assignment().completed(False).filter(
            user=request.user
        ).order_by('-created').first()
        if not assignment:
            task = IdentificationTask.objects.backlog(user=request.user).first()
            if not task:
                return Response(status=status.HTTP_204_NO_CONTENT)
            task.assign_to_user(user=request.user)
            assignment = ExpertReportAnnotation.objects.completed(False).get(
                identification_task=task,
                user=request.user
            )

        serializer = self.get_serializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=self._get_location_header(serializer.data))

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name="MetaCreateIdentificationTaskReview",
            serializers={
                CreateAgreeReviewSerializer().fields['action'].get_default(): CreateAgreeReviewSerializer,
                CreateOverwriteReviewSerializer().fields['action'].get_default(): CreateOverwriteReviewSerializer,
            },
            resource_type_field_name="action",
        ),
        responses={
            201: OpenApiResponse(
                response=IdentificationTaskSerializer.IdentificationTaskReviewSerializer
            )
        }
    )
    @action(detail=True, methods=["POST"], permission_classes=[IdentificationTaskReviewPermissions,])
    def review(self, request, *args, **kwargs):
        task = self.get_object()

        review_type = self.request.data.get("action")
        agree_value = CreateAgreeReviewSerializer().fields['action'].get_default()
        overwrite_value = CreateOverwriteReviewSerializer().fields['action'].get_default()
        if review_type == agree_value:
            serializer_klass = CreateAgreeReviewSerializer
        elif review_type == overwrite_value:
            serializer_klass = CreateOverwriteReviewSerializer
        else:
            raise ValidationError(
                f"Invalid 'review_type'. Must be '{agree_value}' or '{overwrite_value}'"
            )

        context = self.get_serializer_context()
        context['report'] = task.report

        serializer = serializer_klass(context=context, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self._get_location_header(serializer.data)

        response_serializer = IdentificationTaskSerializer.IdentificationTaskReviewSerializer(serializer.instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def _get_location_header(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="observation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the Observation"
            )
        ]
    )
    class PhotoPredictionViewSet(IdentificationTaskNestedAttribute, NestedViewSetMixin, CreateModelMixin, RetrieveModelMixin, ListModelMixin, UpdateModelMixin, DestroyModelMixin, GenericNoMobileViewSet):
        queryset = PhotoPrediction.objects.all().select_related("taxon")
        permission_classes = (PhotoPredictionPermissions, )

        parent_lookup_kwargs = {
            'observation_uuid': 'identification_task__pk'
        }

        lookup_field = 'photo__uuid'
        lookup_url_kwarg = 'photo_uuid'

        def get_serializer_class(self):
            if self.request.method == 'POST':
                return CreatePhotoPredictionSerializer
            return PhotoPredictionSerializer

        def get_serializer_context(self):
            result = super().get_serializer_context()
            result['observation_uuid'] = self.kwargs['observation_uuid']
            return result


    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="observation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the Observation"
            )
        ]
    )
    class AnnotationViewSet(IdentificationTaskNestedAttribute, NestedViewSetMixin, ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericNoMobileViewSet):
        queryset = ExpertReportAnnotation.objects.is_annotation().select_related(
            'user',
            'report',
            'best_photo',
            'taxon',
        ).prefetch_related('tags').annotate(
            is_favourite=models.Exists(
                FavoritedReports.objects.filter(
                    user=models.OuterRef('user'),
                    report=models.OuterRef('report')
                )
            )
        ).annotate(
            report_pk_str=models.functions.Cast('report_id', output_field=models.CharField()),
        )

        serializer_class = AnnotationSerializer
        filter_backends = (DjangoFilterBackend, SearchFilter)
        filterset_class = AnnotationFilter
        search_fields = ("report_pk_str",) #NOTE: not filtering by 'report__report_id' because in not being shown in the response.
        permission_classes = (AnnotationPermissions | UserRolePermission, )

        parent_lookup_kwargs = {
            'observation_uuid': 'identification_task__pk'
        }

        lookup_field = 'pk'
        lookup_url_kwarg = 'id'

        def get_serializer_context(self):
            result = super().get_serializer_context()
            result['observation_uuid'] = self.kwargs['observation_uuid']
            return result

        def create(self, request, *args, **kwargs):
            # Check if it was assigned only (not completed)
            pending_annotation = ExpertReportAnnotation.objects.is_assignment().completed(False).filter(
                identification_task_id=self.kwargs['observation_uuid'],
                user=request.user
            ).first()
            if pending_annotation:
                # Update values
                serializer = self.get_serializer(pending_annotation, data=request.data, partial=False)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                # Mimic creation response
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

            return super().create(request, *args, **kwargs)

@extend_schema_view(
    list=extend_schema(
        tags=['identification-tasks'],
        operation_id='identificationtasks_list_mine',
        description="Get identification tasks annotated by me"
    )
)
class MyIdentificationTaskViewSet(IdentificationTaskViewSet):
    permission_classes = (MyIdentificationTaskPermissions,)

    def get_queryset(self):
        return super().get_queryset().annotated_by(users=[self.request.user,])


@extend_schema_view(
    list=extend_schema(
        tags=['identification-tasks'],
        operation_id='identificationtasks_annotations_list_mine',
        description="Get my annotations"
    )
)
class MyAnnotationViewSet(ListModelMixin, GenericNoMobileViewSet):
    queryset = IdentificationTaskViewSet.AnnotationViewSet.queryset
    serializer_class = IdentificationTaskViewSet.AnnotationViewSet.serializer_class
    filter_backends = IdentificationTaskViewSet.AnnotationViewSet.filter_backends
    filterset_class = IdentificationTaskViewSet.AnnotationViewSet.filterset_class
    search_fields = IdentificationTaskViewSet.AnnotationViewSet.search_fields
    permission_classes = (MyAnnotationPermissions, )

    lookup_field = 'pk'
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class TaxaViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Taxon.objects.all()
    serializer_class = TaxonSerializer
    filterset_class = TaxonFilter
    permission_classes = (TaxaPermissions, )

    @extend_schema(operation_id='taxa_root_tree_retrieve')
    @action(detail=False, methods=["GET"], url_path="tree", serializer_class=TaxonTreeNodeSerializer)
    def root_tree(self, request):
        taxon = Taxon.get_root()
        serializer = self.get_serializer(taxon)
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], url_path="tree", serializer_class=TaxonTreeNodeSerializer)
    def tree(self, request, pk=None):
        taxon = self.get_object()
        serializer = self.get_serializer(taxon)
        return Response(serializer.data)
