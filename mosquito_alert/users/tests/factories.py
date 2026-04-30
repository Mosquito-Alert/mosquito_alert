from factory import Faker, post_generation
from factory.django import DjangoModelFactory
from typing import Sequence, Any

from django.contrib.auth import get_user_model

from mosquito_alert.users.models import TigaUser

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker("user_name")
    first_name = Faker("name")
    last_name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)


class TigaUserFactory(DjangoModelFactory):
    class Meta:
        model = TigaUser

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        if extracted:
            self.set_password(extracted)


def create_regular_user(password: str = "testpassword123_tmp") -> User:
    return UserFactory(password=password)


def create_mobile_user(password: str = "testpassword123_tmp") -> TigaUser:
    return TigaUserFactory(password=password)
