import factory
import factory.fuzzy
from django.db.models.signals import m2m_changed

from mosquito_alert.breeding_sites.tests.factories import BreedingSiteFactory
from mosquito_alert.geo.tests.factories import GeoLocatedModelFactory
from mosquito_alert.identifications.signals import create_dummy_prediction
from mosquito_alert.users.tests.factories import UserFactory

from ..models import BiteReport, BreedingSiteReport, IndividualReport, Report


class ReportFactory(GeoLocatedModelFactory):
    user = factory.SubFactory(UserFactory)

    notes = factory.Faker("paragraph")

    @factory.post_generation
    def photos(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of photos were passed in, use them
            deleted = m2m_changed.disconnect(create_dummy_prediction, sender=self._meta.model.photos.through)
            for photo in extracted:
                self.photos.add(photo)

            if deleted:
                m2m_changed.connect(create_dummy_prediction, sender=self._meta.model.photos.through)

    class Meta:
        model = Report


class BiteReportFactory(ReportFactory):
    @factory.post_generation
    def bites(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of bites were passed in, use them
            for bite in extracted:
                self.bites.add(bite)

    class Meta:
        model = BiteReport


class BreedingSiteReportFactory(ReportFactory):
    breeding_site = factory.SubFactory(BreedingSiteFactory)

    has_water = False

    class Meta:
        model = BreedingSiteReport


class IndividualReportFactory(ReportFactory):
    @classmethod
    def _create(cls, model_class, mute_signals=True, *args, **kwargs):
        if mute_signals:
            m2m_changed.disconnect(create_dummy_prediction, sender=cls._meta.model.photos.through)
        try:
            instance = super()._create(model_class, *args, **kwargs)
        finally:
            m2m_changed.connect(create_dummy_prediction, sender=cls._meta.model.photos.through)
        return instance

    @factory.post_generation
    def individuals(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.individuals.set(extracted)

    class Meta:
        model = IndividualReport
