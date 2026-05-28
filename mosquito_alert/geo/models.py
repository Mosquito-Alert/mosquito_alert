from datetime import timedelta
from difflib import SequenceMatcher
from typing import Optional
import uuid

from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.utils import timezone


class Continent(models.TextChoices):
    AFRICA = "africa", "Africa"
    ANTARCTICA = "antarctica", "Antarctica"
    ASIA = "asia", "Asia"
    EUROPE = "europe", "Europe"
    NORTH_AMERICA = "north_america", "North America"
    OCEANIA = "oceania", "Oceania"
    SOUTH_AMERICA = "south_america", "South America"
    SEVEN_SEAS = "seven_seas", "Seven Seas (open ocean)"

    @classmethod
    def get_by_most_similar_name(cls, name: str) -> Optional["Continent"]:
        if not name:
            return None

        return max(
            cls,  # iterate enum members directly
            key=lambda c: SequenceMatcher(None, name.lower(), c.label.lower()).ratio(),
        )


class Subregion(models.Model):
    continent = models.CharField(max_length=30, choices=Continent.choices)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Country(models.Model):
    # See: https://www.naturalearthdata.com/downloads/10m-cultural-vectors/

    subregion = models.ForeignKey(
        Subregion, related_name="countries", on_delete=models.PROTECT, null=True
    )

    name_engl = models.CharField(
        max_length=44, help_text="Full name of the country in English (e.g., Spain)."
    )
    iso3_code = models.CharField(
        max_length=3,
        unique=True,
        help_text="ISO 3166-1 alpha-3 country code (3-letter code, e.g., ESP).",
    )
    wikidata_id = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^Q\d+$",
                message="Wikidata ID must start with 'Q' followed by digits (e.g., Q29).",
            )
        ],
    )
    geom = models.MultiPolygonField()

    class Meta:
        ordering = ["name_engl"]
        db_table = "europe_countries"
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name_engl


class NutsEurope(models.Model):
    SOURCE_NAME = "NUTS"

    gid = models.AutoField(primary_key=True)
    nuts_id = models.CharField(max_length=5)
    levl_code = models.SmallIntegerField()
    cntr_code = models.CharField(max_length=2, blank=True, null=True)
    name_latn = models.CharField(max_length=70)
    nuts_name = models.CharField(max_length=106)
    mount_type = models.SmallIntegerField(blank=True, null=True)
    urbn_type = models.SmallIntegerField(blank=True, null=True)
    coast_type = models.SmallIntegerField(blank=True, null=True)
    fid = models.CharField(max_length=5, unique=True)
    geom = models.MultiPolygonField(blank=True, null=True)
    europecountry = models.ForeignKey(
        Country,
        blank=True,
        null=True,
        related_name="nuts",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return "{0} ({1})".format(self.name_latn, self.europecountry.name_engl)

    @property
    def code(self) -> str:
        return self.fid

    @property
    def name(self) -> str:
        return self.name_latn.split("/")[0]

    @property
    def level(self) -> int:
        return self.levl_code

    class Meta:
        db_table = "nuts_europe"


class LauEurope(models.Model):
    # NOTE: Lau is equivalent to NUTS 4

    SOURCE_NAME = NutsEurope.SOURCE_NAME

    gid = models.AutoField(primary_key=True)
    lau_id = models.CharField(max_length=13)
    lau_name = models.CharField(max_length=80)
    gisco_id = models.CharField(max_length=16, null=True, blank=True)
    cntr_id = models.CharField(max_length=2, null=True, blank=True)
    fid = models.CharField(max_length=16, unique=True)
    geom = models.MultiPolygonField(null=True, blank=True)

    @property
    def code(self) -> str:
        return self.fid

    @property
    def name(self) -> str:
        def split_and_reverse(string: str) -> str:
            return " ".join(reversed(string.split(",")))

        # Check for conditions where the name needs to be reversed
        should_reverse = False
        if "," in self.lau_name:
            if self.cntr_id == "UK" and "of" in self.lau_name.lower():
                should_reverse = True
            elif self.cntr_id == "ES":
                should_reverse = True
            elif self.cntr_id == "DE" and "stadt" in self.lau_id.lower():
                should_reverse = True

        # Apply the name transformation if needed
        if should_reverse:
            return split_and_reverse(self.lau_name).title()
        return self.lau_name

    @property
    def level(self) -> int:
        return 4

    class Meta:
        db_table = "lau_rg_01m_2018_4326"


class TemporaryBoundary:
    DEFAULT_TTL = 60  # in seconds

    def __init__(self, geometry: GEOSGeometry):
        if not isinstance(geometry, (Polygon, MultiPolygon)):
            raise ValueError("Geometry must be a Polygon or MultiPolygon")
        self.geometry = geometry

        self.uuid: Optional[uuid.UUID] = None
        self.expires_at: Optional[timezone.datetime] = None

    def save(self) -> None:
        boundary_uuid = uuid.uuid4()
        cache.set(str(boundary_uuid), self.geometry.wkt, timeout=self.DEFAULT_TTL)
        self.uuid = boundary_uuid
        self.expires_at = timezone.now() + timedelta(seconds=self.DEFAULT_TTL)

    @property
    def expires_in(self) -> Optional[int]:
        if self.expires_at is None:
            return None
        delta = self.expires_at - timezone.now()
        return max(int(delta.total_seconds()), 0)

    @classmethod
    def get(cls, uuid: "uuid.UUID") -> "TemporaryBoundary":
        cached_wkt = cache.get(str(uuid))
        if cached_wkt is None:
            raise ValueError("No geometry found for the given UUID or it has expired.")

        instance = cls(geometry=GEOSGeometry(cached_wkt))
        instance.uuid = uuid
        return instance
