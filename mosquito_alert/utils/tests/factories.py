import factory
from factory.django import DjangoModelFactory

from .models import DummyObservableModel, DummyTimeStampedModel


class DummyTimeStampedModelFactory(DjangoModelFactory):
    class Meta:
        model = DummyTimeStampedModel


class DummyObservableModelFactory(DjangoModelFactory):
    name = factory.fuzzy.FuzzyText(length=12, prefix="")
    hidden_name = factory.fuzzy.FuzzyText(length=12, prefix="")

    class Meta:
        model = DummyObservableModel
