import uuid

import reversion
from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ProcessedImageField
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager

from mosquito_alert.bites.models import Bite
from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.geo.models import Location
from mosquito_alert.individuals.models import Individual, Taxon

# from polymorphic.managers import PolymorphicManager
# from .querysets import ReportQuerySet


class Report(PolymorphicModel):
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

    # Attributes - Mandatory
    # TODO About uuid: https://stackoverflow.com/questions/3936182/using-a-uuid-as-a-primary-key-in-django-models-generic-relations-impact  # noqa: E501
    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    # NOTE: in case licensing is needed, get inspiration from django-licensing (it does not work)
    # license = models.ForeignKey(License, on_delete=models.PROTECT)
    location = models.OneToOneField(
        Location,
        on_delete=models.PROTECT,
        related_name="report",
        help_text=_("The location where the report is created."),
    )
    # TODO: location_is_modified or another location for the event_location.
    # positional_accuracy = models.IntegerField(
    #     help_text=_("The uncertainty in meters around the latitude and longitude.")
    # )
    observed_at = models.DateTimeField(default=timezone.now, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # TODO: app_version, os

    # Attributes - Optional
    note = models.TextField(null=True, blank=True)

    # Object Manager
    # objects = PolymorphicManager.from_queryset(ReportQuerySet)()
    tags = TaggableManager(
        blank=True,
        help_text=_(
            "A comma-separated list of tags you can add to a report to make them easier to find."
        ),
    )

    # Custom Properties
    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("report")
        verbose_name_plural = _("reports")
        ordering = ["-created_at"]


class ReportPhoto(models.Model):
    # TODO: https://github.com/matthewwithanm/django-imagekit
    # Relations
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="photos")

    # Attributes - Mandatory
    # TODO ?: method field -> seen, caught, trapped, etc
    uuid = models.UUIDField(primary_key=True)
    image = ProcessedImageField(upload_to="photos", format="JPEG")  # Forcing JPEG

    # Attributes - Optional
    # Object Manager

    # Custom Properties
    @property
    def license(self):
        return self.report.license

    # Methods

    # Meta and String
    class Meta:
        verbose_name = _("photo")
        verbose_name_plural = _("photos")


@reversion.register(follow=("report_ptr",))
class BiteReport(Report):

    # Relations
    bites = models.ManyToManyField(Bite, related_name="reports")

    # Attributes - Mandatory

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    # Meta and String
    class Meta:
        verbose_name = _("bite report")
        verbose_name_plural = _("bite reports")


@reversion.register(follow=("report_ptr",))
class BreedingSiteReport(Report):
    # Relations
    breeding_site = models.ForeignKey(
        BreedingSite, blank=True, on_delete=models.CASCADE, related_name="reports"
    )

    # Attributes - Mandatory
    has_water = models.BooleanField()

    # Attributes - Optional
    # Object Manager
    # Custom Properties
    # Methods
    def save(self, *args, **kwargs):
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
    # TODO make photos required and not null!
    "An individual report records an encounter with an individual organism at a particular time and location."
    # Relations
    individual = models.ForeignKey(
        Individual, on_delete=models.CASCADE, related_name="reports"
    )
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
