from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import CreateModelMixin
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny

from mosquito_alert.api.v1.serializers.boundaries import TemporaryBoundarySerializer
from mosquito_alert.api.v1.views.viewsets import GenericViewSet


@extend_schema_view(
    create=extend_schema(
        tags=["boundaries"],
        operation_id="boundaries_create_temporary",
        description="Create a temporary boundary",
    )
)
class BoundaryViewSet(CreateModelMixin, GenericViewSet):
    serializer_class = TemporaryBoundarySerializer

    parser_classes = (JSONParser,)
    permission_classes = (AllowAny,)
