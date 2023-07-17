import factory
from factory.django import DjangoModelFactory, ImageField

from mosquito_alert.users.tests.factories import UserFactory

from ..models import Photo


class PhotoFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    image = ImageField()

    class Meta:
        model = Photo
