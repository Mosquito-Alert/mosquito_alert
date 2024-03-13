from typing import Any, Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from .models import TigaUser

class AppUserBackend:
    def get_user(self, user_id: str) -> Optional[AbstractBaseUser]:
        try:
            return TigaUser._default_manager.get(pk=user_id)
        except TigaUser.DoesNotExist:
            return None

    def authenticate(self, request: HttpRequest, uuid: Optional[str] = None, device_token: Optional[str] = None, **kwargs: Any) -> Optional[AbstractBaseUser]:
        try:
            return TigaUser._default_manager.get(pk=uuid, device_token=device_token)
        except TigaUser.DoesNotExist:
            return None
