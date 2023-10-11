import math
import random
import uuid
from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone
from geopy.distance import distance
from pyproj import Geod
from reversion import create_revision
from reversion.models import Version

from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.breeding_sites.tests.factories import BreedingSiteFactory
from mosquito_alert.geo.tests.fuzzy import FuzzyPoint
from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import BiteReport, BreedingSiteReport, IndividualReport, Report
from .factories import BiteReportFactory, BreedingSiteReportFactory, IndividualReportFactory, ReportFactory


def create_random_point_at_distance(center_point, distance_meters):
    azimuth = random.random() * 2 * math.pi

    # See https://pyproj4.github.io/pyproj/stable/api/geod.html#pyproj.Geod.fwd
    geod = Geod(a=center_point.srs.semi_major, b=center_point.srs.semi_minor)
    lon, lat, _ = geod.fwd(
        lons=center_point.x,
        lats=center_point.y,
        az=azimuth,
        dist=distance_meters,
        radians=False,
    )

    return Point(x=lon, y=lat, srid=center_point.srid)


def test_create_random_point_at_distance():
    point = FuzzyPoint(srid=4326).fuzz()
    new_point = create_random_point_at_distance(center_point=point, distance_meters=1000)

    assert round(distance((point.y, point.x), (new_point.y, new_point.x)).meters) == 1000


@pytest.mark.django_db
class TestReport(BaseTestTimeStampedModel):
    model = Report
    factory_cls = ReportFactory

    # fields
    def test_user_can_be_null(self):
        assert self.model._meta.get_field("user").null

    def test_user_can_be_blank(self):
        assert self.model._meta.get_field("user").blank

    def test_user_is_not_editable(self):
        assert not self.model._meta.get_field("user").editable

    def test_user_set_null_on_delete(self):
        _on_delete = self.model._meta.get_field("user").remote_field.on_delete
        assert _on_delete == models.SET_NULL

    def test_user_related_name(self):
        assert self.model._meta.get_field("user").remote_field.related_name == "reports"

    def test_photos_can_be_blank(self):
        assert self.model._meta.get_field("photos").blank

    def test_photos_can_be_sorted(self):
        assert self.model._meta.get_field("photos").sorted

    def test_uuid_raise_if_set_and_not_uuid(self):
        with pytest.raises(ValidationError, match=r"is not a valid UUID"):
            self.factory_cls(uuid="random_string")

    def test_uuid_default_is_uuid4(self):
        assert self.model._meta.get_field("uuid").default == uuid.uuid4

    def test_uuid_is_not_editable(self):
        assert not self.model._meta.get_field("uuid").editable

    def test_uuid_must_be_unique(self):
        assert self.model._meta.get_field("uuid").unique

    def test_observed_at_can_not_be_null(self):
        assert not self.model._meta.get_field("observed_at").null

    def test_observed_at_can_be_blank(self):
        assert self.model._meta.get_field("observed_at").blank

    @pytest.mark.freeze_time
    def test_observed_at_is_kept_when_set(self):
        observed_at = timezone.now() - timedelta(days=1)
        obj = self.factory_cls(observed_at=observed_at)
        assert obj.observed_at == observed_at

    @pytest.mark.freeze_time
    def test_observed_at_copy_created_at_if_not_set(self):
        created_at = timezone.now() - timedelta(days=1)
        obj = self.factory_cls(observed_at=None, created_at=created_at)
        assert obj.observed_at == created_at

    def test_published_can_not_be_null(self):
        assert not self.model._meta.get_field("published").null

    def test_published_default_value_is_False(self):
        assert not self.model._meta.get_field("published").default

    def test_notes_can_be_null(self):
        assert self.model._meta.get_field("notes").null

    def test_notes_can_be_blank(self):
        assert self.model._meta.get_field("notes").blank

    def test_tags_are_empty_by_default(self):
        assert self.factory_cls().tags.count() == 0

    # meta
    def test_ordering_shows_newest_first(self):
        assert self.model._meta.ordering == ["-created_at"]

    def test__str__(self):
        obj = self.factory_cls()
        assert obj.__str__() == f"{obj.__class__.__name__} ({obj.uuid})"

    @pytest.mark.freeze_time
    def test_observed_at_must_be_before_created_at(self):
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            self.factory_cls(
                observed_at=timezone.now() + timedelta(seconds=10),
            )


class BaseTestReversionedReport:
    def test_report_is_versioned_in_create(self):
        with create_revision():
            obj = self.factory_cls()

        assert Version.objects.get_for_object(obj).count() == 1

    def test_report_is_versioned_in_update(self):
        with create_revision():
            obj = self.factory_cls(notes="v1")

        with create_revision():
            obj.notes = "v2"
            obj.save()

        assert Version.objects.get_for_object(obj)[0].field_dict["notes"] == "v2"
        assert Version.objects.get_for_object(obj)[1].field_dict["notes"] == "v1"

    def test_report_version_deletions(self):
        with create_revision():
            obj = self.factory_cls()

        obj.delete()

        assert Version.objects.get_deleted(obj.__class__).count() == 1

    def test_report_can_be_reverted(self):
        with create_revision():
            obj = self.factory_cls(notes="v1")

        with create_revision():
            obj.notes = "v2"
            obj.save()

        Version.objects.get_for_object(obj)[1].revision.revert()

        obj.refresh_from_db()

        assert obj.notes == "v1"


class TestBiteReport(BaseTestReversionedReport, TestReport):
    model = BiteReport
    factory_cls = BiteReportFactory

    # Tests override
    def test_published_default_value(self):
        assert self.factory_cls().published

    # fields
    def test_bites_related_name(self):
        assert self.model._meta.get_field("bites").remote_field.related_name == "reports"


class TestBreedingSiteReport(BaseTestReversionedReport, TestReport):
    model = BreedingSiteReport
    factory_cls = BreedingSiteReportFactory

    # Tests override
    def test_published_default_value(self):
        assert self.factory_cls().published

    # Custom tests
    def test_breeding_site_can_be_blank(self):
        assert self.model._meta.get_field("breeding_site").blank

    def test_breeding_site_can_not_be_null(self):
        assert not self.model._meta.get_field("breeding_site").null

    def test_breeding_site_deletion_is_cascade(self):
        _on_delete = self.model._meta.get_field("breeding_site").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_breeding_site_related_name(self):
        assert self.model._meta.get_field("breeding_site").remote_field.related_name == "reports"

    def test_has_water_can_not_be_null(self):
        assert not self.model._meta.get_field("has_water").null

    def test_breeding_site_blank_creates_new_breeding_site_if_not_near_found(self):
        assert BreedingSite.objects.all().count() == 0
        report = self.factory_cls(breeding_site=None)

        assert report.breeding_site is not None
        assert BreedingSite.objects.all().count() == 1

    @pytest.mark.parametrize(
        "point",
        [Point(x=random.uniform(-180, 180), y=float(lat), srid=4326) for lat in range(-90, 90, 5)],
    )
    def test_breeding_site_blank_sets_nearest_object_in_50meters(self, point):
        BreedingSiteFactory(location__point=create_random_point_at_distance(center_point=point, distance_meters=100))
        nearest_b_s = BreedingSiteFactory(
            location__point=create_random_point_at_distance(center_point=point, distance_meters=20)
        )
        BreedingSiteFactory(location__point=create_random_point_at_distance(center_point=point, distance_meters=40))

        report = self.factory_cls(location__point=point, breeding_site=None)

        assert report.breeding_site == nearest_b_s

    @pytest.mark.parametrize(
        "point",
        [Point(x=random.uniform(-180, 180), y=float(lat), srid=4326) for lat in range(-90, 90, 5)],
    )
    def test_breeding_site_blank_creates_new_if_no_near_objects_found_in_50meteres(self, point):
        far_b_s = BreedingSiteFactory(
            location__point=create_random_point_at_distance(center_point=point, distance_meters=100)
        )

        report = self.factory_cls(location__point=point, breeding_site=None)

        assert report.breeding_site is not None
        assert report.breeding_site != far_b_s


class TestIndividualReport(BaseTestReversionedReport, TestReport):
    model = IndividualReport
    factory_cls = IndividualReportFactory

    # Custom tests
    def test_individuals_related_name(self):
        assert self.model._meta.get_field("individuals").remote_field.related_name == "reports"

    def test_taxon_can_be_null(self):
        assert self.model._meta.get_field("taxon").null

    def test_taxon_can_be_blank(self):
        assert self.model._meta.get_field("taxon").blank

    def test_taxon_deletion_is_protected(self):
        _on_delete = self.model._meta.get_field("taxon").remote_field.on_delete
        assert _on_delete == models.PROTECT
