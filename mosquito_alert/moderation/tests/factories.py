import factory
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory

from ..models import Flag, FlagInstance
from .testapp.models import DummyFlagModeratedModel, DummyModel


class DummyModelFactory(DjangoModelFactory):
    class Meta:
        model = DummyModel


class FlagFactory(DjangoModelFactory):
    object_id = factory.SelfAttribute("content_object.id")
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))

    content_object = factory.SubFactory(DummyModelFactory)

    class Meta:
        model = Flag


class FlagInstanceFactory(DjangoModelFactory):
    flag = factory.SubFactory(FlagFactory)
    reason = factory.Faker("random_element", elements=FlagInstance.Reason.values)
    notes = factory.Faker("paragraph")

    class Meta:
        model = FlagInstance


class BaseFlagModeratedModelFactory(DjangoModelFactory):
    @factory.post_generation
    def flags(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.flags.set(extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # flags is already set. Do not call obj.save againg
        if results:
            _ = results.pop("flags", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)

    class Meta:
        abstract = True


##########################################################


class DummyFlagModeratedModelFactory(BaseFlagModeratedModelFactory):
    class Meta:
        model = DummyFlagModeratedModel
