import uuid

import reversion
from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from sortedm2m.fields import SortedManyToManyField
from taggit.managers import TaggableManager

from mosquito_alert.bites.models import Bite
from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.geo.models import GeoLocatedModel, Location
from mosquito_alert.images.models import Photo
from mosquito_alert.individuals.models import Individual
from mosquito_alert.moderation.models import FlagModeratedModel
from mosquito_alert.tags.models import UUIDTaggedItem
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.utils.fields import ShortIDField
from mosquito_alert.utils.models import TimeStampedModel

from .managers import IndividualReportManager, ReportManager


# NOTE: FlagModeratedModel uses UUID as pk
class Report(GeoLocatedModel, FlagModeratedModel, TimeStampedModel, PolymorphicModel):
    """A detailed account of an event, based on what one has observed or asked questions about.

    Args:
        models (_type_): _description_
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    photos = SortedManyToManyField(Photo, blank=True)

    # Attributes - Mandatory
    # NOTE: in case licensing is needed, get inspiration from django-licensing (it does not work)
    # license = models.ForeignKey(License, on_delete=models.PROTECT)
    short_id = ShortIDField(size=10, editable=False)
    # TODO: add location_is_modified or another location for the event_location.
    observed_at = models.DateTimeField(blank=True)  # TODO: rename to event_datetime
    published = models.BooleanField(default=False)  # TODO: make it published_at
    # TODO: app_version, os

    # Attributes - Optional
    notes = models.TextField(null=True, blank=True)

    # Object Manager
    objects = ReportManager()
    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_("A comma-separated list of tags you can add to a report to make them easier to find."),
    )

    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.observed_at = self.observed_at or self.created_at
        super().save(*args, **kwargs)

    # Meta and String
    class Meta(GeoLocatedModel.Meta, FlagModeratedModel.Meta, TimeStampedModel.Meta):
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]
        constraints = TimeStampedModel.Meta.constraints + [
            models.CheckConstraint(
                check=models.Q(observed_at__lte=models.F("created_at")),
                name="observed_at_cannot_be_after_created_at",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.id})"


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
                    # Duplicate the location object without saving it yet
                    # This is because it's a OneToOneRelation
                    new_location = Location.objects.get(pk=self.location.pk)
                    new_location.pk = None  # Set primary key to None to create a new object
                    new_location.save()  # Save the duplicated location

                    self.breeding_site = BreedingSite.objects.create(
                        location=new_location,
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
    objects = IndividualReportManager()
    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("report of an individual")
        verbose_name_plural = _("individual reports")
