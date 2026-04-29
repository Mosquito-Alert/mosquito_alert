import factory
from factory.django import DjangoModelFactory

from django.db.models.signals import post_save

from mosquito_alert.workspaces.tests.factories import WorkspaceFactory

from ..models import EuropeCountry

from .fuzzy import FuzzyMultiPolygon


class EuropeCountryFactory(DjangoModelFactory):
    cntr_id = factory.Sequence(lambda n: "%s" % n)
    name_engl = factory.Faker("country")
    iso3_code = factory.Sequence(lambda n: "%s" % n)
    fid = factory.Sequence(lambda n: "%s" % n)
    geom = FuzzyMultiPolygon(srid=4326)

    class Meta:
        model = EuropeCountry


@factory.django.mute_signals(post_save)
class EuropeCountryWithoutSignalsFactory(EuropeCountryFactory):
    workspace = factory.RelatedFactory(WorkspaceFactory, factory_related_name="country")

    class Meta:
        model = EuropeCountry
