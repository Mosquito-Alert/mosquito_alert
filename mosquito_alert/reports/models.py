import uuid

import reversion
from django.conf import settings
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator
from django.db.models.functions import Now
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from sortedm2m.fields import SortedManyToManyField
from taggit.managers import TaggableManager

from mosquito_alert.bites.models import Bite
from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.geo.models import GeoLocatedModel
from mosquito_alert.images.models import Photo
from mosquito_alert.individuals.models import Individual
from mosquito_alert.moderation.models import FlagModeratedModel
from mosquito_alert.taxa.models import Taxon

from .managers import ReportManager


class Report(PolymorphicModel, GeoLocatedModel, FlagModeratedModel):
    """A detailed account of an event, based on what one has observed or asked questions about.

    Args:
        models (_type_): _description_
    """

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
    )
    photos = SortedManyToManyField(Photo, blank=True)

    # Attributes - Mandatory
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    # NOTE: in case licensing is needed, get inspiration from django-licensing (it does not work)
    # license = models.ForeignKey(License, on_delete=models.PROTECT)
    # TODO: add location_is_modified or another location for the event_location.
    observed_at = models.DateTimeField(
        default=timezone.now,
        blank=True,  # TODO: why blank?
        validators=[MaxValueValidator(limit_value=timezone.now)],
    )
    created_at = models.DateTimeField(auto_now_add=True, validators=[MaxValueValidator(limit_value=timezone.now)])
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)
    # TODO: app_version, os

    # Attributes - Optional
    notes = models.TextField(null=True, blank=True)

    # Object Manager
    objects = ReportManager()
    tags = TaggableManager(
        blank=True,
        help_text=_("A comma-separated list of tags you can add to a report to make them easier to find."),
    )

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(created_at__lte=Now()),
                name="created_at_cannot_be_future_dated",
            ),
            models.CheckConstraint(
                check=models.Q(observed_at__lte=models.F("created_at")),
                name="observed_at_cannot_be_after_created_at",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.uuid})"


@reversion.register(follow=("report_ptr",))
class BiteReport(Report):
    # Relations
    bites = models.ManyToManyField(Bite, related_name="reports")

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.published = True
        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("bite report")
        verbose_name_plural = _("bite reports")


@reversion.register(follow=("report_ptr",))
class BreedingSiteReport(Report):
    # Relations
    breeding_site = models.ForeignKey(BreedingSite, blank=True, on_delete=models.CASCADE, related_name="reports")

    # Attributes - Mandatory
    has_water = models.BooleanField()

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.published = True

            if not hasattr(self, "breeding_site"):
                nearest_breeding_site = BreedingSite.objects.within_circle(
                    center_point=self.location.point, radius_meters=50
                ).first_by_distance(point=self.location.point)

                if nearest_breeding_site:
                    self.breeding_site = nearest_breeding_site
                else:
                    self.breeding_site = BreedingSite.objects.create(
                        location=self.location,
                        # TODO: missing breeding_site type
                    )

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        verbose_name = _("breeding site report")
        verbose_name_plural = _("breeding site reports")


@reversion.register(follow=("report_ptr",))
class IndividualReport(Report):
    "An individual report records an encounter with an individual organism at a particular time and location."
    # Relations
    individuals = models.ManyToManyField(Individual, related_name="reports")
    taxon = models.ForeignKey(Taxon, null=True, blank=True, on_delete=models.PROTECT)

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("report of an individual")
        verbose_name_plural = _("individual reports")
