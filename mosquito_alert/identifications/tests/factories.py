from abc import abstractmethod

import factory
import factory.fuzzy
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory

from mosquito_alert.annotations.tests.factories import (
    BaseAnnotationFactory,
    BaseAnnotatorProfileFactory,
    BasePhotoAnnotationTaskFactory,
    BaseTaskFactory,
    RectangularShapeFactory,
)
from mosquito_alert.taxa.tests.factories import TaxonFactory

from ..models import (
    BaseClassification,
    BaseTaskResult,
    ExternalIdentification,
    IdentifierProfile,
    IndividualIdentificationTask,
    IndividualIdentificationTaskResult,
    PhotoIdentificationTask,
    PhotoIdentificationTaskResult,
    Prediction,
    TaxonClassificationCandidate,
    UserIdentification,
)
from ..prob_tree import TaxonProbNode
from .models import DummyBaseClassification


class TaxonProbNodeFactory(factory.Factory):
    taxon = factory.SubFactory(TaxonFactory)
    probability = factory.fuzzy.FuzzyDecimal(low=0.01, high=1, precision=6)

    # parent
    # children
    class Meta:
        model = TaxonProbNode


##########################
# User Profile
##########################


class IdentifierProfileFactory(BaseAnnotatorProfileFactory):
    class Meta:
        model = IdentifierProfile


#############################
class BaseTaxonAnnotationFactory(BaseAnnotationFactory):
    label = factory.SubFactory(TaxonFactory)
    probability = factory.fuzzy.FuzzyDecimal(low=0, high=1, precision=6)

    class Meta:
        abstract = True


class BaseClassificationFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    sex = factory.fuzzy.FuzzyChoice(BaseClassification.SexOptions.values)

    @factory.post_generation
    def candidates(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.candidates.set(extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # candidates is already set. Do not call obj.save againg
        if results:
            _ = results.pop("candidates", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)


class DummyClassificationFactory(BaseClassificationFactory):
    class Meta:
        model = DummyBaseClassification


class TaxonClassificationCandidateFactory(BaseTaxonAnnotationFactory):
    object_id = factory.SelfAttribute("content_object.pk")
    content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object))

    content_object = factory.SubFactory(DummyClassificationFactory)

    class Meta:
        # exclude = ["content_object"]
        model = TaxonClassificationCandidate


class BaseIdentificationFactory(RectangularShapeFactory, BaseClassificationFactory):
    class Meta:
        abstract = True


##########################
# Task definition
##########################


class BaseTaskWithResultsFactory(BaseTaskFactory):
    class Meta:
        abstract = True


class BaseTaskChildFactory(DjangoModelFactory):
    @property
    @abstractmethod
    def task(self):
        raise NotImplementedError

    class Meta:
        abstract = True


class IndividualIdentificationTaskFactory(BaseTaskWithResultsFactory):
    # We pass in identification_task=None to prevent IndividualFactory from creating another identification task
    # (this disables the RelatedFactory)
    individual = factory.SubFactory(
        "mosquito_alert.individuals.tests.factories.IndividualFactory", identification_task=None
    )

    class Meta:
        model = IndividualIdentificationTask


class PhotoIdentificationTaskFactory(BasePhotoAnnotationTaskFactory, BaseTaskWithResultsFactory):
    task = factory.SubFactory(IndividualIdentificationTaskFactory)

    class Meta:
        model = PhotoIdentificationTask


##########################
# Identification definition
##########################


class BasePhotoIdentificationFactory(BaseIdentificationFactory, BaseTaskChildFactory):
    task = factory.SubFactory(PhotoIdentificationTaskFactory)

    class Meta:
        abstract = True


class UserIdentificationFactory(BasePhotoIdentificationFactory):
    identifier_profile = factory.SubFactory(IdentifierProfileFactory)

    class Meta:
        model = UserIdentification


class PredictionFactory(BasePhotoIdentificationFactory):
    class Meta:
        model = Prediction


class ExternalIdentificationFactory(BasePhotoIdentificationFactory):
    class Meta:
        model = ExternalIdentification


##########################
# Task Results
##########################


class BaseTaskResultFactory(BaseTaskChildFactory):
    type = factory.Faker("random_element", elements=BaseTaskResult.ResultType.values)

    class Meta:
        abstract = True


class BaseClassificationTaskResultFactory(
    BaseTaxonAnnotationFactory, BaseClassificationFactory, BaseTaskResultFactory
):
    class Meta:
        abstract = True


class BaseIdentificationTaskResultFactory(RectangularShapeFactory, BaseClassificationTaskResultFactory):
    class Meta:
        abstract = True


class IndividualIdentificationTaskResultFactory(BaseClassificationTaskResultFactory):
    task = factory.SubFactory(IndividualIdentificationTaskFactory)

    class Meta:
        model = IndividualIdentificationTaskResult


class PhotoIdentificationTaskResultFactory(RectangularShapeFactory, BaseClassificationTaskResultFactory):
    task = factory.SubFactory(PhotoIdentificationTaskFactory)

    class Meta:
        model = PhotoIdentificationTaskResult

    @factory.post_generation
    def user_identifications(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.user_identifications.set(extracted)

    @factory.post_generation
    def predictions(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.predictions.set(extracted)

    @factory.post_generation
    def external_identifications(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, do nothing
            return

        obj.external_identifications.set(extracted)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        # identifications is already set. Do not call obj.save againg
        if results:
            _ = results.pop("user_identifications", None)
            _ = results.pop("predictions", None)
            _ = results.pop("external_identifications", None)
        super()._after_postgeneration(instance=instance, create=create, results=results)
