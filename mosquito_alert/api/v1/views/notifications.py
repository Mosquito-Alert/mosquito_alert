from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin

from mosquito_alert.api.v1.filters import NotificationFilter
from mosquito_alert.api.v1.permissions import (
    MyNotificationPermissions,
    NotificationObjectPermissions,
)
from mosquito_alert.api.v1.serializers.notifications import NotificationSerializer
from mosquito_alert.api.v1.viewsets import GenericMobileOnlyViewSet
from mosquito_alert.notifications.models import NotificationRecipient
from mosquito_alert.users.models import TigaUser


class NotificationViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericMobileOnlyViewSet,
):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NotificationFilter
    serializer_class = NotificationSerializer

    permission_classes = (NotificationObjectPermissions,)

    lookup_field = "notification_id"
    lookup_url_kwarg = "id"

    queryset = NotificationRecipient.objects.select_related(
        "notification", "notification__notification_content"
    ).all()

    def get_queryset(self):
        qs = super().get_queryset()

        user = self.request.user
        if isinstance(user, TigaUser):
            qs = qs.filter(user=user)

        return qs


@extend_schema_view(
    list=extend_schema(
        tags=["notifications"],
        operation_id="notifications_list_mine",
        description="Get Current User's Notifications",
    )
)
class MyNotificationViewSet(NotificationViewSet, ListModelMixin):
    permission_classes = (MyNotificationPermissions,)
