from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin

from mosquito_alert.api.v1.serializers.devices import (
    DeviceSerializer,
    DeviceUpdateSerializer,
)
from mosquito_alert.api.v1.views.viewsets import GenericMobileOnlyViewSet
from mosquito_alert.devices.models import Device


class DeviceViewSet(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericMobileOnlyViewSet
):
    queryset = (
        Device.objects.filter(device_id__isnull=False)
        .exclude(device_id="")
        .select_related("mobile_app")
    )
    serializer_class = DeviceSerializer

    lookup_field = "device_id"
    lookup_url_kwarg = "device_id"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return DeviceUpdateSerializer
        return super().get_serializer_class()
