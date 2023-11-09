import factory
from django.db.models.signals import post_save
from factory.django import DjangoModelFactory

from mosquito_alert.identifications.models import IndividualIdentificationTaskResult
from mosquito_alert.identifications.signals import create_identification_task_on_individual_creation
from mosquito_alert.identifications.tests.factories import (
    IndividualIdentificationTaskFactory,
    IndividualIdentificationTaskResultFactory,
)

from ..models import Individual


class IndividualFactory(DjangoModelFactory):
    # We pass in 'individual' to link the generated Individual to our just-generated IdentificationTask
    # This will call IndividualIdentificationTaskFactory(individual=our_new_individual), thus skipping the SubFactory.
    identification_task = factory.RelatedFactory(
        IndividualIdentificationTaskFactory, factory_related_name="individual"
    )

    @classmethod
    def _create(cls, model_class, mute_signals=True, *args, **kwargs):
        if mute_signals:
            post_save.disconnect(create_identification_task_on_individual_creation, sender=cls._meta.model)
        try:
            instance = super()._create(model_class, *args, **kwargs)
        finally:
            post_save.connect(create_identification_task_on_individual_creation, sender=cls._meta.model)
        return instance

    @factory.post_generation
    def taxon(self, create, extracted, **kwargs):
        if not create:
            return

        # If taxon is defined on create
        if extracted:
            _ = IndividualIdentificationTaskResultFactory(
                task=self.identification_task,
                type=IndividualIdentificationTaskResult.ResultType.ENSEMBLED,
                label=extracted,
                probability=1,
            )

    class Meta:
        model = Individual
