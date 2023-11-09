import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from flag.models import Flag, FlagInstance

from mosquito_alert.users.tests.factories import UserFactory

from ..models import FlagModeratedModel
from .testapp.models import DummyFlagModeratedModel


class FlagFactory(DjangoModelFactory):
    object_id = factory.SelfAttribute("content_object.id")
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))

    creator = factory.SubFactory(UserFactory)
    state = factory.Faker("random_element", elements=[x[0] for x in Flag.STATE_CHOICES])
    moderator = factory.SubFactory(UserFactory)

    class Meta:
        exclude = ["content_object"]
        model = Flag

    class Params:
        is_banned = factory.Trait(state=factory.Faker("random_element", elements=FlagModeratedModel.IS_BANNED_STATES))

        is_permitted = factory.Trait(
            state=factory.Faker(
                "random_element", elements=list(set(Flag.State) - set(FlagModeratedModel.IS_BANNED_STATES))
            )
        )


class FlagInstanceFactory(DjangoModelFactory):
    flag = factory.SubFactory(FlagFactory)
    user = factory.SubFactory(UserFactory)
    reason = factory.Faker("random_element", elements=FlagInstance.REASON)
    info = factory.Faker("paragraph")

    class Meta:
        model = FlagInstance


##########################################################


class DummyFlagModeratedModelFactory(DjangoModelFactory):
    flags = factory.RelatedFactory(FlagFactory, factory_related_name="content_object")

    class Meta:
        model = DummyFlagModeratedModel

    class Params:
        is_banned = factory.Trait(flags__is_banned=True)
        is_permitted = factory.Trait(flags__is_permitted=True)
