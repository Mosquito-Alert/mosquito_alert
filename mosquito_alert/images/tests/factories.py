import factory
from factory.django import ImageField

from mosquito_alert.moderation.tests.factories import BaseFlagModeratedModelFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import Photo


class PhotoFactory(BaseFlagModeratedModelFactory):
    user = factory.SubFactory(UserFactory)
    image = ImageField()

    class Meta:
        model = Photo
