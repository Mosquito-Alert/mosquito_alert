import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from mosquito_alert.individuals.tests.factories import IndividualFactory
from mosquito_alert.taxa.tests.factories import TaxonFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import (
    ComputerVisionIdentificationSuggestion,
    IdentificationResult,
    IdentifierUserProfile,
    ImageTaxonPrediction,
    ImageTaxonPredictionRun,
    UserIdentificationSuggestion,
)


##########################
# Abstract Models
##########################
class BaseIdentificationCandidateFactory(DjangoModelFactory):
    taxon = factory.SubFactory(TaxonFactory)
    probability = factory.fuzzy.FuzzyFloat(low=0, high=1)

    class Meta:
        abstract = True


class BaseIndividualIdentificationCandidateFactory(BaseIdentificationCandidateFactory):
    individual = factory.SubFactory(IndividualFactory)

    class Meta:
        abstract = True


##########################
# User Profile
##########################


class IdentifierUserProfileFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = IdentifierUserProfile
        django_get_or_create = [
            "user",
        ]


##########################
# Individual Probability Tree Identification Models
##########################


class IdentificationResultFactory(
    BaseIndividualIdentificationCandidateFactory, DjangoModelFactory
):
    type = factory.Faker(
        "random_element", elements=IdentificationResult.IdentificationResultType.values
    )

    class Meta:
        model = IdentificationResult


##########################
# Individual Single Identification Models
##########################


class UserIdentificationSuggestionFactory(BaseIndividualIdentificationCandidateFactory):
    user_profile = factory.SubFactory(IdentifierUserProfileFactory)
    probability = factory.Faker(
        "random_element",
        elements=UserIdentificationSuggestion.IdentificationConfidence.values,
    )

    class Meta:
        model = UserIdentificationSuggestion


class ComputerVisionIdentificationSuggestionFactory(
    BaseIndividualIdentificationCandidateFactory
):
    class Meta:
        model = ComputerVisionIdentificationSuggestion


##########################
# AI Prediction Models
##########################


class ImageTaxonPredictionRunFactory(DjangoModelFactory):
    # photo = factory.SubFactory() # TODO

    class Meta:
        model = ImageTaxonPredictionRun


class ImageTaxonPredictionFactory(BaseIdentificationCandidateFactory):
    prediction_run = factory.SubFactory(ImageTaxonPredictionRunFactory)

    class Meta:
        model = ImageTaxonPrediction
