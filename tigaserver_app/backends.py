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

    def authenticate(self, request: HttpRequest, uuid: str = None, password: str = None, **kwargs: Any) -> Optional[AbstractBaseUser]:
        if uuid is None or password is None:
            return

        try:
            user = TigaUser._default_manager.get(pk=uuid)
        except TigaUser.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            TigaUser().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        return getattr(user, "is_active", True)