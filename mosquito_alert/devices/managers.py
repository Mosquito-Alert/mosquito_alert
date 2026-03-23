
from fcm_django.models import FCMDeviceQuerySet, FCMDeviceManager


class DeviceQuerySet(FCMDeviceQuerySet):
    def deactivate_devices_with_error_results(self, *args, **kwargs):
        deactivated_ids = super().deactivate_devices_with_error_results(*args, **kwargs)

        self.filter(registration_id__in=deactivated_ids).update(active_session=False)

        return deactivated_ids

class DeviceManager(FCMDeviceManager):
    def get_queryset(self):
        return DeviceQuerySet(self.model)
