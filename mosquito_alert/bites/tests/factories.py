import factory
from factory.django import DjangoModelFactory

from mosquito_alert.individuals.tests.factories import IndividualFactory

from ..models import Bite


class BiteFactory(DjangoModelFactory):
    individual = factory.SubFactory(IndividualFactory)
    body_part = factory.Faker("random_element", elements=Bite.BodyParts.values)

    class Meta:
        model = Bite
