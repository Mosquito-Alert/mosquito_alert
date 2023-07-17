from django.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.taxa.models import MonthlyDistribution as TaxaMonthlyDistribution
from mosquito_alert.taxa.models import Taxon

from .managers import MonthlyDistributionManager


class Disease(models.Model):
    # Relations

    # Attributes - Mandatory
    name = models.CharField(max_length=64, unique=True)

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("disease")
        verbose_name_plural = _("diseases")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DiseaseVector(models.Model):
    # Relations
    taxon = models.OneToOneField(
        Taxon,
        on_delete=models.CASCADE,
        related_name="disease_vector",
        limit_choices_to={"rank__gte": Taxon.TaxonomicRank.SPECIES_COMPLEX},
    )
    diseases = models.ManyToManyField(Disease, related_name="disease_vectors")

    # Attributes - Mandatory
    # Attributes - Optional
    # Object Manager

    # Custom Properties

    # Methods
    def save(self, *args, **kwargs):
        if not self.taxon.is_specie:
            raise ValueError("Taxon must be species rank.")

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("disease vector")
        verbose_name_plural = _("disease vectors")
        ordering = ["taxon__name"]

    def __str__(self) -> str:
        return self.taxon.name


class MonthlyDistribution(TaxaMonthlyDistribution):
    objects = MonthlyDistributionManager()

    class Meta:
        proxy = True
        verbose_name = _("monthly distribution")
        verbose_name_plural = _("monthly distributions")
