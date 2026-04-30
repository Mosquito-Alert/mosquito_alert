import factory
from factory.django import DjangoModelFactory

from mosquito_alert.reports.tests.factories import ObservationReportWithoutSignalFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import ExpertReportAnnotation, IdentificationTask


class IdentificationTaskFactory(DjangoModelFactory):
    class Meta:
        model = IdentificationTask

    # We pass in identification_task=None to prevent IndividualFactory from creating another identification task
    # (this disables the RelatedFactory)
    report = factory.SubFactory(
        ObservationReportWithoutSignalFactory, identification_task=None
    )
    photo = factory.LazyAttribute(lambda o: o.report.photos.first())


class ExpertReportAnnotationFactory(DjangoModelFactory):
    class Meta:
        model = ExpertReportAnnotation

    user = factory.SubFactory(UserFactory)
    identification_task = factory.SubFactory(IdentificationTaskFactory)

    decision_level = ExpertReportAnnotation.DecisionLevel.NORMAL

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.tags.add(*extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # tags is already set. Do not call obj.save againg
        if results:
            _ = results.pop("tags", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)
