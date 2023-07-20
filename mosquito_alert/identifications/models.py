from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE, AFTER_DELETE, AFTER_UPDATE, LifecycleModelMixin, hook

from mosquito_alert.images.models import Photo
from mosquito_alert.individuals.models import Individual
from mosquito_alert.taxa.models import Taxon

from .managers import IdentificationResultManager
from .mixins import (
    IdentificationResultProxyMixin,
    MultipleIndividualIdentificationCandidateMixin,
    ProbabilityTreeModelMixin,
)
from .prob_tree import create_tree_from_identifications


##########################
# Abstract Models
##########################
class BaseIdentificationCandidate(ProbabilityTreeModelMixin, models.Model):
    # Relations
    taxon = models.ForeignKey(Taxon, on_delete=models.PROTECT)

    # Attributes - Mandatory
    probability = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    # Attributes - Optional

    # Object Manager

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.taxon} (p={self.probability})"


class BaseIndividualIdentificationCandidate(BaseIdentificationCandidate):
    # Relations
    individual = models.ForeignKey(Individual, on_delete=models.CASCADE)

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods

    class Meta:
        abstract = True


class MultipleIdentificationCandidateModel(
    MultipleIndividualIdentificationCandidateMixin,
    BaseIndividualIdentificationCandidate,
):
    class Meta:
        abstract = True


##########################
# User Profile
##########################
class IdentifierUserProfile(models.Model):
    # Relations
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    # TODO: reviewed_individuals = models.ManyToManyField(Individual)

    # Attributes - Mandatory
    # TODO: role?
    is_superexpert = models.BooleanField(default=False)
    # precision = models.FloatField(
    #    default=0.5, validators=[MinValueValidator(0), MaxValueValidator(1)]
    # )  # TODO: Keep historic of weights? Select weight according to identification updated_date

    # Attributes - Optional

    # Object Manager

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("identifier user profile")
        verbose_name_plural = _("identifier user profiles")

    def __str__(self) -> str:
        return str(self.user)


##########################
# Individual Probability Tree Identification Models
##########################
class IdentificationResult(MultipleIdentificationCandidateModel):
    class IdentificationResultType(models.TextChoices):
        COMMUNITY = "com", _("Community")  # User based only
        ENSEMBLED = "ens", _("Ensembled")  # User + AI based

    # Relations

    # Attributes - Mandatory
    type = models.CharField(max_length=3, choices=IdentificationResultType.choices)

    # Attributes - Optional

    # Object Manager
    objects = IdentificationResultManager()

    # Custom Properties
    # Methods

    grouped_by_fields = MultipleIdentificationCandidateModel.grouped_by_fields + [
        "type"
    ]  # Needed for MultipleIdentificationCandidateModel

    @classmethod
    def _check_type(cls, value):
        if value not in cls.IdentificationResultType.values:
            raise ValueError(f"{value} is not an allowed type value: ({cls.IdentificationResultType.values})")

    @classmethod
    def get_probability_tree(cls, individual, type):
        cls._check_type(value=type)

        return super().get_probability_tree(individual=individual, type=type)

    @classmethod
    def get_probability_for_taxon(cls, taxon, individual, type):
        cls._check_type(value=type)

        return super().get_probability_for_taxon(taxon=taxon, individual=individual, type=type)

    @classmethod
    def _update_from_tree(cls, tree, individual, type):
        cls._check_type(value=type)

        super()._update_from_tree(tree=tree, individual=individual, type=type)

        if type == cls.IdentificationResultType.ENSEMBLED:
            if consensus := IdentificationResult.objects.get_consensus(
                individual=individual, type=cls.IdentificationResultType.ENSEMBLED
            ):
                individual.taxon = consensus.taxon
                individual.save()

    @classmethod
    def _update_by_type(cls, individual, type):
        def get_community_result_tree(individual=individual):
            user_profiles = IdentifierUserProfile.objects.filter(identifications__individual=individual)

            if not user_profiles.exists():
                return

            # TODO: change weight to user's identification precision/weight
            weight_factor = 1 / user_profiles.count()
            return sum(
                [
                    UserIdentificationSuggestion.get_probability_tree(
                        individual=individual, user_profile=x
                    ).apply_weight(weight=weight_factor)
                    for x in user_profiles
                ]
            )

        cls._check_type(value=type)

        result_tree = None

        superexpert_suggestion = UserIdentificationSuggestion.objects.filter(
            user_profile__is_superexpert=True, individual=individual
        )
        if superexpert_suggestion.exists():
            result_tree = UserIdentificationSuggestion.get_probability_tree(
                individual=individual,
                user_profile=superexpert_suggestion.first().user_profile,
            )
        else:
            if type == cls.IdentificationResultType.COMMUNITY:
                result_tree = get_community_result_tree(individual=individual)
                if not result_tree:
                    return
            elif type == cls.IdentificationResultType.ENSEMBLED:
                community_result_tree = IdentificationResult.get_probability_tree(
                    type=cls.IdentificationResultType.COMMUNITY, individual=individual
                )

                computer_vision_result_tree = ComputerVisionIdentificationSuggestion.get_probability_tree(
                    individual=individual
                )

                if community_result_tree and computer_vision_result_tree:
                    result_tree = community_result_tree.apply_weight(
                        weight=0.7
                    ) + computer_vision_result_tree.apply_weight(weight=0.3)
                else:
                    result_tree = community_result_tree or computer_vision_result_tree
                    if not result_tree:
                        return

        IdentificationResult._update_from_tree(individual=individual, type=type, tree=result_tree)

        if type == cls.IdentificationResultType.COMMUNITY:
            IdentificationResult._update_by_type(individual=individual, type=cls.IdentificationResultType.ENSEMBLED)

    @classmethod
    def update(cls, individual, type=None):
        # If updating community, ensembled needs to be updated too.
        type = type or cls.IdentificationResultType.COMMUNITY
        cls._check_type(value=type)

        cls._update_by_type(individual=individual, type=type)

    # Meta and String
    class Meta:
        verbose_name = _("identification result")
        verbose_name_plural = _("identification results")
        default_related_name = "identification_results"
        constraints = [
            models.UniqueConstraint(
                fields=["individual", "type", "taxon"],
                name="unique_taxon_individual_type",
            )
        ]


class CommunityIdentificationResult(IdentificationResultProxyMixin, IdentificationResult):
    RESULT_TYPE = IdentificationResult.IdentificationResultType.COMMUNITY

    class Meta:
        proxy = True
        verbose_name = _("community identification result")
        verbose_name_plural = _("community identification results")


class EnsembledIdentificationResult(IdentificationResultProxyMixin, IdentificationResult):
    RESULT_TYPE = IdentificationResult.IdentificationResultType.ENSEMBLED

    class Meta:
        proxy = True
        verbose_name = _("ensembled identification result")
        verbose_name_plural = _("ensembled identification results")


##########################
# Individual Single Identification Models
##########################
class BaseIdentificationResultChild(LifecycleModelMixin, BaseIndividualIdentificationCandidate):
    PARENT_RESULT_MODEL = None  # instance of BaseIdentificationResultProxy

    @hook(AFTER_CREATE)
    @hook(AFTER_DELETE)
    @hook(AFTER_UPDATE, when_any=["probability", "taxon"], has_changed=True)
    def _update_parent_result(self):
        self.PARENT_RESULT_MODEL.update(individual=self.individual)

    class Meta:
        abstract = True


class BaseIdentificationSuggestion(BaseIdentificationResultChild):
    # Relations

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional

    # Object Manager

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        abstract = True


class UserIdentificationSuggestion(MultipleIndividualIdentificationCandidateMixin, BaseIdentificationSuggestion):
    PARENT_RESULT_MODEL = CommunityIdentificationResult

    grouped_by_fields = MultipleIdentificationCandidateModel.grouped_by_fields + [
        "user_profile"
    ]  # Needed for MultipleIdentificationCandidateModel

    class IdentificationConfidence(float, models.Choices):
        HIGH = 1.0, _("I'm sure")
        MEDIUM = 0.75, _("I'm doubting.")

    # Relations
    user_profile = models.ForeignKey(
        IdentifierUserProfile,
        null=True,
        on_delete=models.SET_NULL,
        related_name="identifications",
    )

    # Attributes - Mandatory
    probability = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        choices=IdentificationConfidence.choices,
    )  # @override: added choices.

    # Attributes - Optional
    notes = models.TextField(null=True, blank=True)

    # Object Manager
    # Custom Properties

    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("user identification suggestion")
        verbose_name_plural = _("user identification suggestions")
        constraints = [
            models.UniqueConstraint(  # Allow single user identification for each individual.
                fields=["user_profile", "individual"],
                name="unique_user_individual",
            )
        ]


class ComputerVisionIdentificationSuggestion(
    MultipleIndividualIdentificationCandidateMixin, BaseIdentificationSuggestion
):
    PARENT_RESULT_MODEL = EnsembledIdentificationResult

    # Relations
    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager
    # Custom Properties

    # Methods
    @classmethod
    def update(cls, individual):
        predictions = ImageTaxonPredictionRun.objects.filter(photo__individuals=individual)

        if not predictions.exists():
            return

        weight_factor = 1 / predictions.count()
        result_tree = sum([x.get_probability_tree().apply_weight(weight=weight_factor) for x in predictions])

        cls._update_from_tree(individual=individual, tree=result_tree)

    # Meta and String
    class Meta:
        verbose_name = _("computer vision identification suggestion")
        verbose_name_plural = _("computer vision identification suggestions")


##########################
# AI Prediction Models
##########################
class ImageTaxonPredictionRun(models.Model):
    # Relations
    photo = models.OneToOneField(Photo, on_delete=models.CASCADE, related_name="taxon_prediction_run")

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: bounding box: https://docs.aws.amazon.com/rekognition/latest/dg/images-displaying-bounding-boxes.html

    # Attributes - Optional
    # Object Manager

    # Custom Properties
    @cached_property
    def individuals(self):
        return self.photo.individuals.all()

    # Methods
    def update_individuals_suggestion(self):
        for individual in self.individuals:
            ComputerVisionIdentificationSuggestion.update(individual=individual)

    def get_probability_tree(self):
        qs = self.image_taxon_predictions
        if not qs.exists():
            return None

        return create_tree_from_identifications([(x.taxon, x.probability) for x in qs.all()])

    # Meta and String
    class Meta:
        verbose_name = _("taxon image prediction run")
        verbose_name_plural = _("taxon image predictions runs")


class ImageTaxonPrediction(BaseIdentificationCandidate):
    # Relations
    prediction_run = models.ForeignKey(
        ImageTaxonPredictionRun,
        on_delete=models.CASCADE,
        related_name="image_taxon_predictions",
    )

    # Attributes - Mandatory

    # Attributes - Optional

    # Object Manager

    # Custom Properties
    # Methods
    # TODO: only call update on last add (bulk)
    @hook(AFTER_CREATE)
    @hook(AFTER_DELETE)
    @hook(AFTER_UPDATE, when_any=["probability", "taxon"], has_changed=True)
    def _notify_prediction_run_update(self):
        self.prediction_run.update_individuals_suggestion()

    # Meta and String
    class Meta:
        verbose_name = _("taxon image prediction")
        verbose_name_plural = _("taxon image prediction")
        constraints = [
            models.UniqueConstraint(  # Allow single taxon suggestion for each prediction run.
                fields=["taxon", "prediction_run"],
                name="unique_taxon_prediction_run",
            )
        ]
        ordering = ["prediction_run", "-probability"]
