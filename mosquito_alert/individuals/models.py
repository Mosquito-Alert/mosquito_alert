from django.conf import settings
from django.db import models
from django.db.models import Min
from django.utils.translation import gettext_lazy as _

from mosquito_alert.images.models import Photo
from mosquito_alert.taxa.models import Taxon


class Individual(models.Model):
    # Relations

    # Attributes - Mandatory
    photos = models.ManyToManyField(Photo, blank=True, related_name="individuals")
    # is_identified = models.BooleanField(default=False)
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
        if self.reports:
            self.reports.aggregate(first=Min("observed_at"))["first"]

        return result

    # Methods
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


class IdentificationSet(models.Model):
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
    agreement = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
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
        MIN_SCORING = 0.75
        scores = self._get_taxa_scoring()
        # Filtering and sort scores
        scores = sorted(
            filter(lambda x: x[1] >= MIN_SCORING, scores), key=lambda x: x[1]
        )
        if scores:
            self.taxon = scores[0][0]
            self.agreement = scores[0][1]
        else:
            self.taxon = self.get_root()
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
