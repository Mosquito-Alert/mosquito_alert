from django.contrib.gis.geos import Point
from django.utils.dateparse import parse_datetime
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

    locale = "en"
    # longitude, latitude (SRID 4326)
    last_location = Point(-3.7038, 40.4168, srid=4326)

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        if extracted:
            self.set_password(extracted)

    @post_generation
    def last_login(self, create: bool, extracted, **kwargs):
        if extracted:
            self.last_login = parse_datetime(extracted)
            if create:
                self.save(update_fields=["last_login"])
