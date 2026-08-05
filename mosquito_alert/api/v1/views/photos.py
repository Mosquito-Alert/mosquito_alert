from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from mosquito_alert.api.v0.serializers import PhotoSerializer
from mosquito_alert.api.v1.serializers.identification_tasks import (
    PhotoPredictionSerializer,
)
from mosquito_alert.api.v1.viewsets import GenericNoMobileViewSet
from mosquito_alert.identification_tasks.models import PhotoPrediction
from mosquito_alert.reports.models import Photo


class PhotoViewSet(RetrieveModelMixin, GenericNoMobileViewSet):
    queryset = Photo.objects.visible()
    serializer_class = PhotoSerializer

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    @action(
        detail=True,
        methods=["GET", "PUT", "PATCH", "DELETE"],
        authentication_classes=GenericNoMobileViewSet.authentication_classes,
        permission_classes=GenericNoMobileViewSet.permission_classes,
        parser_classes=GenericViewSet.parser_classes,
        serializer_class=PhotoPredictionSerializer,
        queryset=PhotoPrediction.objects.all().select_related("taxon"),
        lookup_field="photo__uuid",
        filter_backends=[],
    )
    def prediction(self, request, uuid=None):
        if request.method == "GET":
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        elif request.method == "POST":
            serializer = self.get_serializer(data=request.data)
            serializer.context["photo__uuid"] = uuid
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self._get_location_header(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )
        elif request.method in ["PUT", "PATCH"]:
            partial = request.method == "PATCH"
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == "DELETE":
            instance = self.get_object()
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def _get_location_header(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}
