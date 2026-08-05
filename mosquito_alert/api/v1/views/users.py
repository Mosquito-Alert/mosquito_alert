import uuid

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin

from mosquito_alert.api.v1.permissions import UserPermissions
from mosquito_alert.api.v1.serializers.users import UserSerializer
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.users.models import TigaUser


User = get_user_model()

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
class UserViewSet(UpdateModelMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    search_fields = ("user_UUID",)

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
        tags=["users"],
        operation_id="users_retrieve_mine",
        description="Get Current User's Profile",
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
