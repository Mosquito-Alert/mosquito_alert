from django.contrib.auth import get_user_model
from django.db import models

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    PolymorphicProxySerializer,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import status
from rest_framework.decorators import (
    action,
)
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
)
from rest_framework.response import Response
from rest_framework.settings import api_settings


from mosquito_alert.identification_tasks.models import (
    IdentificationTask,
    ExpertReportAnnotation,
    PhotoPrediction,
)
from mosquito_alert.reports.models import Photo

from mosquito_alert.api.v1.filters import (
    IdentificationTaskFilter,
    AnnotationFilter,
)
from mosquito_alert.api.v1.mixins import IdentificationTaskNestedAttribute
from mosquito_alert.api.v1.serializers import (
    AnnotationSerializer,
    AssignmentSerializer,
    IdentificationTaskSerializer,
    PhotoPredictionSerializer,
    CreatePhotoPredictionSerializer,
    CreateAgreeReviewSerializer,
    CreateOverwriteReviewSerializer,
)
from mosquito_alert.api.v1.permissions import (
    IdentificationTaskPermissions,
    MyIdentificationTaskPermissions,
    IdentificationTaskAssignmentPermissions,
    IdentificationTaskReviewPermissions,
    IdentificationTaskCapabilitiesPermissions,
    AnnotationPermissions,
    MyAnnotationPermissions,
    PhotoPredictionPermissions,
)
from mosquito_alert.api.v1.viewsets import (
    GenericNoMobileViewSet,
    NestedViewSetMixin,
)

User = get_user_model()


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
class IdentificationTaskViewSet(
    RetrieveModelMixin, ListModelMixin, GenericNoMobileViewSet
):
    queryset = (
        IdentificationTask.objects.all()
        .select_related(
            "taxon",
            "photo",
            "report",
            "report__user",
            "report__country",
            # NOTE: needed for get_display_name
            "report__nuts_2_fk",
            "report__nuts_3_fk",
            "report__lau_fk",
        )
        .prefetch_related(
            # NOTE: used in serializers for 'assignments' field.
            models.Prefetch(
                "expert_report_annotations",
                queryset=ExpertReportAnnotation.objects.all().select_related("user"),
            ),
            models.Prefetch(
                "report__photos",
                queryset=Photo.objects.visible(),
            ),
        )
    )
    serializer_class = IdentificationTaskSerializer
    filterset_class = IdentificationTaskFilter
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("report__report_id", "report__version_UUID")
    permission_classes = (IdentificationTaskPermissions,)

    lookup_field = "pk"
    lookup_url_kwarg = IDENTIFICATION_TASK_VIEW_LOOKUP_FIELD

    def get_queryset(self):
        is_capabilities = self.action == "capabilities"

        qs = (
            super()
            .get_queryset()
            .browsable(user=self.request.user, include_assigned=is_capabilities)
        )

        if is_capabilities:
            qs = qs.select_related(None).prefetch_related(None).order_by()

        return qs

    @extend_schema(
        request=None,
        responses={
            201: AssignmentSerializer,
            204: OpenApiResponse(description="No available tasks pending to assign"),
        },
        operation_id="identificationtasks_assign_next",
        description="Assign the next available identification task.",
    )
    @action(
        detail=False,
        methods=[
            "POST",
        ],
        url_path="assignments/next",
        permission_classes=[
            IdentificationTaskAssignmentPermissions,
        ],
        serializer_class=AssignmentSerializer,
    )
    def assign_next(self, request):
        # Checking if there are any assignments with pending annotation for that user.
        assignment = (
            ExpertReportAnnotation.objects.completed(False)
            .filter(user=request.user)
            .order_by("-created")
            .first()
        )
        if not assignment:
            task = IdentificationTask.objects.backlog(user=request.user).first()
            if not task:
                return Response(status=status.HTTP_204_NO_CONTENT)
            task.assign_to_user(user=request.user)
            assignment = ExpertReportAnnotation.objects.completed(False).get(
                identification_task=task, user=request.user
            )

        serializer = self.get_serializer(assignment)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self._get_location_header(serializer.data),
        )

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name="MetaCreateIdentificationTaskReview",
            serializers={
                list(CreateAgreeReviewSerializer().fields["action"].choices.values())[
                    0
                ]: CreateAgreeReviewSerializer,
                list(
                    CreateOverwriteReviewSerializer().fields["action"].choices.values()
                )[0]: CreateOverwriteReviewSerializer,
            },
            resource_type_field_name="action",
        ),
        responses={
            201: OpenApiResponse(
                response=IdentificationTaskSerializer.IdentificationTaskReviewSerializer
            )
        },
    )
    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[
            IdentificationTaskReviewPermissions,
        ],
    )
    def review(self, request, *args, **kwargs):
        task = self.get_object()

        context = self.get_serializer_context()
        context["identification_task"] = task

        review_type = self.request.data.get("action")
        agree_value = list(
            CreateAgreeReviewSerializer().fields["action"].choices.values()
        )[0]
        overwrite_value = list(
            CreateOverwriteReviewSerializer().fields["action"].choices.values()
        )[0]
        if review_type == agree_value:
            serializer = CreateAgreeReviewSerializer(context=context, data=request.data)
        elif review_type == overwrite_value:
            # Check if already exist and ExpertAnnotationReport. If so, update (pass to serializer)
            try:
                annotation = ExpertReportAnnotation.objects.filter(
                    user=request.user, identification_task=task
                ).latest("created")
            except ExpertReportAnnotation.DoesNotExist:
                annotation = None
            serializer = CreateOverwriteReviewSerializer(
                instance=annotation, context=context, data=request.data
            )
        else:
            raise ValidationError(
                f"Invalid 'review_type'. Must be '{agree_value}' or '{overwrite_value}'"
            )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        headers = self._get_location_header(serializer.data)

        task.refresh_from_db()
        response_serializer = (
            IdentificationTaskSerializer.IdentificationTaskReviewSerializer(task)
        )
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(
        detail=True,
        methods=["GET"],
        serializer_class=IdentificationTaskSerializer.IdentificationTaskCapabilitiesSerializer,
        permission_classes=[IdentificationTaskCapabilitiesPermissions],
    )
    def capabilities(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    def _get_location_header(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="observation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the Observation",
            )
        ]
    )
    class PhotoPredictionViewSet(
        IdentificationTaskNestedAttribute,
        NestedViewSetMixin,
        CreateModelMixin,
        RetrieveModelMixin,
        ListModelMixin,
        UpdateModelMixin,
        DestroyModelMixin,
        GenericNoMobileViewSet,
    ):
        queryset = PhotoPrediction.objects.all().select_related("taxon")
        permission_classes = (PhotoPredictionPermissions,)
        serializer_class = PhotoPredictionSerializer

        parent_lookup_kwargs = {"observation_uuid": "identification_task__pk"}

        lookup_field = "photo__uuid"
        lookup_url_kwarg = "photo_uuid"

        def get_serializer_class(self):
            if self.request.method == "POST":
                return CreatePhotoPredictionSerializer
            return super().get_serializer_class()

        def get_serializer_context(self):
            result = super().get_serializer_context()
            result["observation_uuid"] = self.kwargs["observation_uuid"]
            return result

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="observation_uuid",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the Observation",
            )
        ]
    )
    class AnnotationViewSet(
        IdentificationTaskNestedAttribute,
        NestedViewSetMixin,
        ListModelMixin,
        RetrieveModelMixin,
        CreateModelMixin,
        GenericNoMobileViewSet,
    ):
        queryset = (
            ExpertReportAnnotation.objects.completed()
            .select_related(
                "user",
                "best_photo",
                "taxon",
            )
            .prefetch_related("tags")
        )

        serializer_class = AnnotationSerializer
        filter_backends = (DjangoFilterBackend, SearchFilter)
        filterset_class = AnnotationFilter
        search_fields = ("identification_task__report__version_UUID",)
        permission_classes = (AnnotationPermissions,)

        parent_lookup_kwargs = {"observation_uuid": "identification_task__pk"}

        lookup_field = "pk"
        lookup_url_kwarg = "id"

        def get_serializer_context(self):
            result = super().get_serializer_context()
            result["observation_uuid"] = self.kwargs["observation_uuid"]
            return result

        def create(self, request, *args, **kwargs):
            identification_task = self.get_identification_task_obj()
            # # Check user has permissions to create an annotation for that observation
            can_create = request.user.has_perm(
                "%(app_label)s.add_%(model_name)s"
                % {
                    "app_label": ExpertReportAnnotation._meta.app_label,
                    "model_name": ExpertReportAnnotation._meta.model_name,
                },
                obj=identification_task,
            )
            if not can_create:
                self.permission_denied(request)

            # Check if it was assigned only (not completed)
            pending_annotation = (
                ExpertReportAnnotation.objects.completed(False)
                .filter(
                    identification_task=identification_task,
                    user=request.user,
                )
                .first()
            )
            if pending_annotation:
                # Update values
                serializer = self.get_serializer(
                    pending_annotation, data=request.data, partial=False
                )
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                # Mimic creation response
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED, headers=headers
                )

            return super().create(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(
        tags=["identification-tasks"],
        operation_id="identificationtasks_list_mine",
        description="Get identification tasks annotated by me",
    )
)
class MyIdentificationTaskViewSet(IdentificationTaskViewSet):
    permission_classes = (MyIdentificationTaskPermissions,)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotated_by(
                users=[
                    self.request.user,
                ]
            )
        )


@extend_schema_view(
    list=extend_schema(
        tags=["identification-tasks"],
        operation_id="identificationtasks_annotations_list_mine",
        description="Get my annotations",
    )
)
class MyAnnotationViewSet(ListModelMixin, GenericNoMobileViewSet):
    queryset = IdentificationTaskViewSet.AnnotationViewSet.queryset
    serializer_class = IdentificationTaskViewSet.AnnotationViewSet.serializer_class
    filter_backends = IdentificationTaskViewSet.AnnotationViewSet.filter_backends
    filterset_class = IdentificationTaskViewSet.AnnotationViewSet.filterset_class
    search_fields = IdentificationTaskViewSet.AnnotationViewSet.search_fields
    permission_classes = (MyAnnotationPermissions,)

    lookup_field = "pk"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
