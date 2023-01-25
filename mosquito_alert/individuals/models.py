from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Min
from django.db.models.signals import ModelSignal
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_UPDATE, LifecycleModel, hook

from mosquito_alert.images.models import Photo
from mosquito_alert.notifications.signals import notify_subscribers
from mosquito_alert.taxa.models import Taxon

post_identification_changed = ModelSignal(use_caching=True)


class Individual(LifecycleModel):
    # Relations

    # Attributes - Mandatory
    is_identified = models.BooleanField(default=False)
    photos = models.ManyToManyField(Photo, blank=True, related_name="individuals")
    # community_taxon_id = models.ForeignKey(Taxon, on_delete=models.PROTECT)
    # identifications_agreements = models.PositiveSmallIntegerField()
    # number_identifications_agreements = models.PositiveIntegerField()
    # reviewed_by = models.ManyToManyField()

    # Attributes - Optional
    # Object Manager

    # Custom Properties
    @property
    def first_observed_at(self):
        result = None
        if hasattr(self, "reports"):
            result = self.reports.aggregate(first=Min("observed_at"))["first"]

        return result

    # Methods
    @hook(AFTER_UPDATE, when="is_identified", was=False, is_now=True)
    def notify_identification(self):

        if hasattr(self, "reports"):
            for r in self.reports.all():
                for b in r.location.boundaries.all():
                    notify_subscribers.send(
                        sender=self.identification_set.taxon,
                        verb="was identified in",
                        target=b,
                    )
        else:
            notify_subscribers.send(
                sender=self.identification_set.taxon,
                verb="was identified",
            )

    def delete(self, *args, **kwargs):
        # TODO delete orphan images with no reports assigne to them.
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs) -> None:

        super().save(*args, **kwargs)

        if not hasattr(self, "identification_set"):
            # Init IdentificationSet
            IdentificationSet.objects.create(
                individual=self,
            )

    # Meta and String
    class Meta:
        verbose_name = _("individual")
        verbose_name_plural = _("individuals")

    def __str__(self) -> str:
        return (
            self.identification_set.taxon.__str__()
            if self.identification_set
            else f"{self.__class__} (pk: {self.pk})"
        )


class IdentificationSet(LifecycleModel):

    MIN_IDENTIFICATION_COUNT = 3
    MIN_AGREEMENT = 0.75

    # Relations
    individual = models.OneToOneField(
        Individual, on_delete=models.CASCADE, related_name="identification_set"
    )
    taxon = models.ForeignKey(
        Taxon,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="identification_sets",
    )

    # Attributes - Mandatory
    agreement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(0),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    @hook(AFTER_UPDATE, when="taxon", has_changed=True, on_commit=True)
    def send_identification_changed_signal(self):
        post_identification_changed.send(sender=self.__class__, instance=self)

    @hook(AFTER_UPDATE, when_any=["taxon", "agreement"], has_changed=True)
    def update_is_identified(self):
        is_species_rank = self.taxon.rank >= Taxon.TaxonomicRank.SPECIES_COMPLEX
        is_over_agreement_level = self.agreement >= self.MIN_AGREEMENT
        if is_species_rank and is_over_agreement_level:
            self.individual.is_identified = True
        else:
            self.individual.is_identified = False

        self.individual.save()

    def _get_taxa_scoring(self):
        result = {}
        counter = 0
        for iden in self.identifications.select_related("taxon").all():
            new_value = iden.confidence / 100  # Weighet by it's confidence
            # Update taxon score
            result[iden.taxon] = result.get(iden.taxon, 0) + new_value
            for taxon in iden.taxon.get_ancestors():
                # Update ancestor score
                result[taxon] = result.get(taxon, 0) + new_value
            counter += 1

        # Divide by the number of identifications
        result = dict(zip(result.keys(), map(lambda x: x / counter, result.values())))
        # Return a list of tuples (taxon, score)
        return list(result.items())

    def _update_identification_result(self):
        scores = self._get_taxa_scoring()
        # Filtering and sort scores
        scores = sorted(scores, key=lambda x: x[1])
        if scores:
            self.taxon = scores[0][0]
            self.agreement = scores[0][1]
        else:
            self.taxon = Taxon.get_root_nodes().first()
            self.agreement = 0
        self.save()

    # Meta and String
    class Meta:
        verbose_name = _("identification set")
        verbose_name_plural = _("identification sets")

    def __str__(self) -> str:
        return self.taxon.__str__()


class Identification(models.Model):
    class IdentificationConfidence(models.IntegerChoices):
        HIGH = 100, _("I'm sure")
        MEDIUM = 75, _("I'm doubting.")
        LOW = 50, _("I've seriously got doubts.")

    # Relations
    identification_set = models.ForeignKey(
        IdentificationSet, on_delete=models.CASCADE, related_name="identifications"
    )
    taxon = models.ForeignKey(
        Taxon, on_delete=models.PROTECT, related_name="identifications"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="identifications",
    )

    # Attributes - Mandatory
    confidence = models.IntegerField(choices=IdentificationConfidence.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    # TODO category field?: supporting, improving, leading
    # Leading: Taxon descends from the community taxon. This identification
    #          could be leading toward the right answer.
    # Improving: First suggestion of this taxon that the community subsequently
    #          agreed with. This identification helped refine the community taxon.
    # Supporting: Taxon is the same as the community taxon. This identification
    #          supports the community ID.
    # Maverick: Taxon is not a descendant or ancestor of the community taxon.
    #           The community does not agree with this identification.

    # Attributes - Optional
    comment = models.TextField(null=True, blank=True)

    # Object Manager

    # Custom Properties

    # Methods
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.identification_set._update_identification_result()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.identification_set._update_identification_result()

    # Meta and String
    class Meta:
        verbose_name = _("identification")
        verbose_name_plural = _("identifications")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "identification_set"],
                name="unique_user_identification_set",
            )
        ]

    def __str__(self) -> str:
        return self.taxon.__str__()


class AnnotationAttribute(models.Model):
    # Relations
    # Those taxon that can be questioned with this anntoations: life, mammals, culex pipiens, etc
    taxa = models.ForeignKey(
        Taxon, on_delete=models.CASCADE, related_name="annotation_attributes"
    )

    # Attributes - Mandatory
    label = models.CharField(max_length=128)  # the question
    # datatype = # TODO: numerics, text, choices

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("annotation attribute")
        verbose_name_plural = _("annotation attributes")

    def __str__(self) -> str:
        return self.label


class AnnotationValue(models.Model):

    # Relations
    annotation_attribute = models.ForeignKey(
        AnnotationAttribute, on_delete=models.CASCADE, related_name="values"
    )
    taxa = models.ForeignKey(
        Taxon, on_delete=models.CASCADE, related_name="annotation_values"
    )  # Those taxon that can be questioned with this anntoations: life, mammals, culex pipiens, etc

    # Attributes - Mandatory
    label = models.CharField(
        max_length=128
    )  # Dead, Alive | egg, pupa (only a set of taxons)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def save(self, *args, **kwargs) -> None:

        if (
            self.taxa != self.annotation_attribute.taxa
            or not self.taxa.is_descendant_of(self.annotation_attribute.taxa)
        ):
            raise ValueError(
                "Tried to assign an annotation value to a taxa that is not "
                "same/descendant of annotation's attribute taxa."
            )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("annotation value")
        verbose_name_plural = _("annotation values")

    def __str__(self) -> str:
        return f"{self.label} ({self.annotation_attribute.label})"


class Annotation(models.Model):

    # Relations
    annotation_attribute = models.ForeignKey(
        AnnotationAttribute, on_delete=models.PROTECT, related_name="annotations"
    )
    annotation_value = models.ForeignKey(
        AnnotationValue, on_delete=models.PROTECT, related_name="annotations"
    )
    individual = models.ForeignKey(
        Individual, on_delete=models.CASCADE, related_name="annotations"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="annotations",
    )

    # Attributes - Mandatory
    created_at = models.DateTimeField(auto_now_add=True)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def save(self, *args, **kwargs) -> None:

        if self.annotation_value not in self.annotation_attribute.values:
            raise ValueError(
                "The annotation value is not a valid option for this annotation attribute."
            )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("annotation")
        verbose_name_plural = _("annotations")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "individual", "annotation_attribute"],
                name="unique_user_individual_annotation-attribute",
            )
        ]

    def __str__(self) -> str:
        return f"{self.annotation_attribute}->{self.annotation_attribute}"
