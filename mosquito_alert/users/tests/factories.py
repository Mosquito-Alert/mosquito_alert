import random

from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from mosquito_alert.users.models import TigaUser


User = get_user_model()


def create_regular_user(password: str = "testpassword123_tmp") -> "User":
    user = User.objects.create_user(
        username=f"user_{random.randint(1, 1000)}",
        password=get_random_string(length=10),
        first_name="Test FirstName",
        last_name="Test LastName",
    )
    if password:
        user.set_password(password)
        user.save()
    return user


def create_mobile_user(password: str = "testpassword123_tmp") -> TigaUser:
    user = TigaUser.objects.create()
    if password:
        user.set_password(password)
        user.save()
    return user
