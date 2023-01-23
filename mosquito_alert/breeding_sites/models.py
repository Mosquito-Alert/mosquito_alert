from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.geo.models import GeoLocatedModel


class BreedingSite(GeoLocatedModel):
    class BreedingSiteTypes(models.TextChoices):
        STORM_DRAIN = "SD", _("Storm drain")

    # Relations

    # Attributes - Mandatory
    type = models.CharField(
        max_length=2, choices=BreedingSiteTypes.choices, null=True, blank=True
    )

    # Attributes - Optional
    # Object Manager
    # NOTE: if ever need to add custom manager, take GeoLocatedModel manager into account.

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("breeding site")
        verbose_name_plural = _("breeding sites")

    def __str__(self) -> str:
        return f"{self.get_type_display()} ({self.location})"
