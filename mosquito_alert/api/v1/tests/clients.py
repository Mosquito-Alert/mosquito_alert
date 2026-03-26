from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

from mosquito_alert.devices.models import Device
from mosquito_alert.users.models import TigaUser

from mosquito_alert.api.v1.auth.serializers import AppUserTokenObtainPairSerializer

User = get_user_model()


class AppAPIClient(APIClient):
    def __init__(self, device: Device = None, *args, **kwargs):
        self.device = device
        super().__init__(self, *args, **kwargs)

    def force_login(self, user, backend=None) -> None:
        self.logout()
        return super().force_login(user, backend)

    def _login(self, user, backend=None):
        if isinstance(user, User):
            return super()._login(user, backend)
        elif isinstance(user, TigaUser):
            token = AppUserTokenObtainPairSerializer.get_token(
                user=user, device_id=self.device.device_id if self.device else None
            )
            self.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
        else:
            raise NotImplementedError
