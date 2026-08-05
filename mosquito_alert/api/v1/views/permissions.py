from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from mosquito_alert.api.v1.serializers.permissions import PermissionsSerializer
from mosquito_alert.api.v1.viewsets import GenericViewSet


@extend_schema_view(
    retrieve=extend_schema(
        tags=["permissions"],
        operation_id="permissions_retrieve_mine",
        description="Get Current User's Permissions",
    )
)
class MyPermissionViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = None
    serializer_class = PermissionsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        # May raise a permission denied
        self.check_object_permissions(self.request, user)

        return user
