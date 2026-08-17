from abc import abstractmethod
from typing import Callable, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import serializers
from rest_framework.decorators import (
    action,
)
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
)
from rest_framework.parsers import FormParser
from rest_framework.permissions import (
    AllowAny,
    SAFE_METHODS,
)
from rest_framework.response import Response

from rest_framework_csv.renderers import CSVStreamingRenderer
from rest_framework_gis.filters import DistanceToPointFilter
from rest_framework_simplejwt.tokens import Token

from mosquito_alert.api.v1.filters import (
    BiteFilter,
    BreedingSiteFilter,
    ObservationFilter,
)
from mosquito_alert.api.v1.parsers import MultiPartJsonNestedParser
from mosquito_alert.api.v1.permissions import MyReportPermissions, ReportPermissions
from mosquito_alert.api.v1.renderers import GeoJsonRenderer
from mosquito_alert.api.v1.serializers.reports import (
    BiteGeoJsonModelSerializer,
    BiteGeoModelSerializer,
    BiteSerializer,
    BreedingSiteGeoJsonModelSerializer,
    BreedingSiteGeoModelSerializer,
    BreedingSiteSerializer,
    ObservationGeoJsonModelSerializer,
    ObservationGeoModelSerializer,
    ObservationSerializer,
)
from mosquito_alert.api.v1.utils import get_serializer_field_paths_for_csv
from mosquito_alert.api.v1.views.viewsets import (
    GenericMobileOnlyViewSet,
    GenericViewSet,
)
from mosquito_alert.devices.models import Device
from mosquito_alert.reports.models import Report, Photo
from mosquito_alert.users.models import TigaUser


User = get_user_model()


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
    # TODO: select_related for identification_task only for observations.
    queryset = (
        Report.objects.select_related(
            "nuts_2_fk",
            "nuts_3_fk",
            "lau_fk",
            "country",
            "identification_task",
            "identification_task__photo",
            "identification_task__taxon",
        )
        .prefetch_related(
            # NOTE: might be solved when start using native django-taggitg class in the model.
            # See bug https://github.com/jazzband/django-taggit/issues/255
            # 'tags',
            models.Prefetch("photos", queryset=Photo.objects.visible())
        )
        .annotate(
            pk_str=models.functions.Cast("pk", output_field=models.CharField()),
        )
        .non_deleted()
        .filter(point__isnull=False)
        .order_by("-server_upload_time")
    )

    lookup_url_kwarg = REPORT_VIEW_LOOKUP_FIELD

    filter_backends = (DjangoFilterBackend, SearchFilter, DistanceToPointFilter)
    search_fields = ("report_id", "pk_str")
    distance_filter_field = "point"
    distance_filter_convert_meters = True

    permission_classes = (ReportPermissions,)

    @property
    @abstractmethod
    def filename_csv(self):
        raise NotImplementedError

    def get_permissions(self):
        # Check if the request is for an action
        if self.action and hasattr(self, self.action):
            action_method = getattr(self, self.action)
            if action_method and hasattr(action_method, "kwargs"):
                action_permissions = action_method.kwargs.get("permission_classes")
                if action_permissions:
                    return [permission() for permission in action_permissions]

        if self.request and self.request.method in SAFE_METHODS:
            return [
                AllowAny(),
            ]

        return super().get_permissions()

    def get_serializer_context(self):
        result = super().get_serializer_context()
        if self.request.user.is_authenticated and isinstance(self.request.user, User):
            # If user has view permissions, never hide.
            result["hide_note_if_not_owner"] = not self.request.user.has_perm(
                f"{Report._meta.app_label}.view_{Report._meta.model_name}"
            )

        return result

    def _geo(
        self,
        request,
        geojson_serializer_class,
        get_queryset: Optional[Callable[[], models.QuerySet]] = None,
        *args,
        **kwargs,
    ):
        if get_queryset is not None:
            queryset = get_queryset()
        else:
            queryset = (
                self.get_queryset()
                .select_related(None)
                .prefetch_related(None)
                .order_by()
            )
        qs = self.filter_queryset(queryset)

        if isinstance(self.request.accepted_renderer, GeoJsonRenderer):
            serializer = geojson_serializer_class(
                qs, many=True, context=self.get_serializer_context()
            )
        else:
            serializer = self.get_serializer(qs, many=True)
        return Response(
            serializer.data, content_type=self.request.accepted_renderer.media_type
        )

    def get_renderers(self):
        renderers = super().get_renderers()
        if self.action == "list":
            return renderers + [
                CSVStreamingRenderer(),
            ]
        return renderers

    def list(self, request, *args, **kwargs):
        # Override list to handle CSV rendering without pagination
        if self.request.accepted_renderer.format == CSVStreamingRenderer.format:
            queryset = self.filter_queryset(self.get_queryset().prefetch_related(None))
            request.accepted_renderer.header = get_serializer_field_paths_for_csv(
                serializer=self.get_serializer(),
                separator=request.accepted_renderer.level_sep,
            )

            response = StreamingHttpResponse(
                request.accepted_renderer.render(
                    self._stream_serialized_data(queryset)
                ),
                content_type=CSVStreamingRenderer.media_type,
            )
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                self.filename_csv
            )
            return response

        return super().list(request, *args, **kwargs)

    def _stream_serialized_data(self, queryset, batch_size=2000):
        serializer_class = self.get_serializer_class()

        # Fields to exclude
        exclude_fields = [
            name
            for name, field in serializer_class().fields.items()
            if isinstance(field, (serializers.ListSerializer, serializers.ListField))
        ]

        batch = []
        for obj in queryset.iterator(chunk_size=batch_size):
            batch.append(obj)
            if len(batch) >= batch_size:
                serializer = self.get_serializer(
                    batch, many=True, exclude_fields=exclude_fields
                )
                yield from serializer.data
                batch = []

        # Serialize any leftover objects
        if batch:
            serializer = self.get_serializer(
                batch, many=True, exclude_fields=exclude_fields
            )
            yield from serializer.data

    def _get_device_from_jwt(self) -> Optional[Device]:
        if not self.request:
            return

        if not isinstance(self.request.auth, Token):
            return

        device_id = self.request.auth.get("device_id")
        if not device_id:
            return

        try:
            return Device.objects.get(user=self.request.user, device_id=device_id)
        except Device.DoesNotExist:
            return

    def perform_create(self, serializer):
        kwargs = {}
        user = self.request.user
        if isinstance(user, TigaUser):
            kwargs["app_language"] = user.locale

        device = self._get_device_from_jwt()
        if device:
            kwargs["device"] = device
            kwargs["device_manufacturer"] = device.manufacturer
            kwargs["device_model"] = device.model
            kwargs["os"] = device.os_name
            kwargs["os_version"] = device.os_version
            kwargs["os_language"] = device.os_locale
            if device.mobile_app:
                kwargs["mobile_app"] = device.mobile_app
                kwargs["package_name"] = device.mobile_app.package_name
                v = device.mobile_app.package_version
                kwargs["package_version"] = int(f"{v.major}{v.minor:02d}")
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        self.perform_create(serializer=serializer)

    def get_queryset(self):
        return super().get_queryset().browsable(user=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()


class BaseMyReportViewSet(BaseReportViewSet, GenericMobileOnlyViewSet):
    def get_permissions(self):
        return [
            MyReportPermissions(),
        ]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class BaseReportWithPhotosViewSet(BaseReportViewSet):
    def get_parsers(self):
        # Since photos are required on POST, only allow
        # parasers that allow files.
        if self.request and self.request.method == "POST":
            return [MultiPartJsonNestedParser(), FormParser()]
        return super().get_parsers()


class BiteViewSet(BaseReportViewSet):
    serializer_class = BiteSerializer
    filterset_class = BiteFilter

    queryset = BaseReportViewSet.queryset.filter(type=Report.TYPE_BITE)

    filename_csv = "bites.csv"

    @extend_schema(
        responses={
            (200, "application/json"): BiteGeoModelSerializer(many=True),
            (200, GeoJsonRenderer.media_type): BiteGeoJsonModelSerializer(many=True),
        }
    )
    @method_decorator(cache_page(60 * 60 * 3))  # Cache for 3 hours
    @method_decorator(vary_on_headers("Authorization"))
    @action(
        detail=False,
        methods=[
            "GET",
        ],
        serializer_class=BiteGeoModelSerializer,
        pagination_class=None,
        renderer_classes=BaseReportViewSet.renderer_classes + (GeoJsonRenderer,),
    )
    def geo(self, request):
        return self._geo(request, geojson_serializer_class=BiteGeoJsonModelSerializer)


@extend_schema_view(
    list=extend_schema(
        tags=["bites"],
        operation_id="bites_list_mine",
        description="Get Current User's Bites",
    )
)
class MyBiteViewSet(BaseMyReportViewSet, BiteViewSet):
    pass


class BreedingSiteViewSet(BaseReportWithPhotosViewSet):
    serializer_class = BreedingSiteSerializer
    filterset_class = BreedingSiteFilter

    queryset = BaseReportWithPhotosViewSet.queryset.filter(type=Report.TYPE_SITE)

    filename_csv = "breeding_sites.csv"

    @extend_schema(
        responses={
            (200, "application/json"): BreedingSiteGeoModelSerializer(many=True),
            (200, GeoJsonRenderer.media_type): BreedingSiteGeoJsonModelSerializer(
                many=True
            ),
        }
    )
    @method_decorator(cache_page(60 * 60 * 3))  # Cache for 3 hours
    @method_decorator(vary_on_headers("Authorization"))
    @action(
        detail=False,
        methods=[
            "GET",
        ],
        serializer_class=BreedingSiteGeoModelSerializer,
        pagination_class=None,
        renderer_classes=BaseReportViewSet.renderer_classes + (GeoJsonRenderer,),
    )
    def geo(self, request):
        return self._geo(
            request, geojson_serializer_class=BreedingSiteGeoJsonModelSerializer
        )


@extend_schema_view(
    list=extend_schema(
        tags=["breeding-sites"],
        operation_id="breedingsites_list_mine",
        description="Get Current User's Breeding Sites",
    )
)
class MyBreedingSiteViewSet(BaseMyReportViewSet, BreedingSiteViewSet):
    pass


class ObservationViewSet(BaseReportWithPhotosViewSet):
    serializer_class = ObservationSerializer
    filterset_class = ObservationFilter

    queryset = BaseReportWithPhotosViewSet.queryset.filter(type=Report.TYPE_ADULT)

    filename_csv = "observations.csv"

    @extend_schema(
        responses={
            (200, "application/json"): ObservationGeoModelSerializer(many=True),
            (200, GeoJsonRenderer.media_type): ObservationGeoJsonModelSerializer(
                many=True
            ),
        }
    )
    @method_decorator(cache_page(60 * 60 * 3))  # Cache for 3 hours
    @method_decorator(vary_on_headers("Authorization"))
    @action(
        detail=False,
        methods=[
            "GET",
        ],
        serializer_class=ObservationGeoModelSerializer,
        pagination_class=None,
        renderer_classes=BaseReportViewSet.renderer_classes + (GeoJsonRenderer,),
    )
    def geo(self, request):
        return self._geo(
            request,
            geojson_serializer_class=ObservationGeoJsonModelSerializer,
            get_queryset=lambda: (
                self.get_queryset()
                .select_related(None)
                .select_related("identification_task")
                .prefetch_related(None)
                .order_by()
            ),
        )


@extend_schema_view(
    list=extend_schema(
        tags=["observations"],
        operation_id="observations_list_mine",
        description="Get Current User's Observations",
    )
)
class MyObservationViewSet(BaseMyReportViewSet, ObservationViewSet):
    pass
