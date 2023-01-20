from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from mosquito_alert.geo.models import Location
from mosquito_alert.geo.querysets import GeoLocatedModelQuerySet


class BreedingSite(models.Model):
    class BreedingSiteTypes(models.TextChoices):
        STORM_DRAIN = "SD", _("Storm drain")

    # Relations

    # Attributes - Mandatory
    location = models.OneToOneField(Location, on_delete=models.PROTECT)
    type = models.CharField(
        max_length=2, choices=BreedingSiteTypes.choices, null=True, blank=True
    )

    # Attributes - Optional
    # Object Manager
    objects = models.Manager.from_queryset(GeoLocatedModelQuerySet)()

    # Custom Properties
    # Methods
    # Meta and String
    class Meta:
        verbose_name = _("breeding site")
        verbose_name_plural = _("breeding sites")

    def __str__(self) -> str:
        return f"{self.get_type_display()} ({self.location})"
