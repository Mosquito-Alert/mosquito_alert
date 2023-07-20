import math
import random
import uuid
from datetime import timedelta

import pytest
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.utils import timezone
from geopy.distance import distance
from pyproj import Geod
from reversion import create_revision
from reversion.models import Version

from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.breeding_sites.tests.factories import BreedingSiteFactory
from mosquito_alert.geo.tests.fuzzy import FuzzyPoint
from mosquito_alert.individuals.tests.factories import IndividualFactory

from ..models import IndividualReport
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
class TestReport:
    @pytest.fixture
    def factory_cls(self):
        return ReportFactory

    @pytest.fixture
    def simple_report(self, factory_cls):
        return factory_cls()

    def test_user_can_be_null(self, factory_cls):
        factory_cls(user=None)

    def test_user_set_null_on_delete(self, simple_report):
        assert simple_report.user is not None

        simple_report.user.delete()
        simple_report.refresh_from_db()

        assert simple_report.user is None

    def test_uuid_raise_if_set_and_not_uuid(self, factory_cls):
        with pytest.raises(ValidationError, match=r"is not a valid UUID"):
            factory_cls(uuid="random_string")

    def test_uuid_is_auto_set_to_uuidv4(self, simple_report):
        assert isinstance(simple_report.uuid, uuid.UUID)
        assert simple_report.uuid.version == 4

    def test_uuid_must_be_unique(self, factory_cls):
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            factory_cls.create_batch(size=2, uuid=uuid.uuid4())

    @pytest.mark.freeze_time
    def test_observed_at_is_now_by_default(self, simple_report):
        assert simple_report.observed_at == timezone.now()

    @pytest.mark.freeze_time
    def test_observed_at_must_be_before_created_at(self, factory_cls):
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            factory_cls(
                observed_at=timezone.now() + timedelta(seconds=10),
            )

    @pytest.mark.freeze_time
    def test_created_at_is_now_by_default(self, simple_report):
        assert simple_report.created_at == timezone.now()

    @pytest.mark.freeze_time
    def test_updated_at_is_now_by_default(self, simple_report):
        assert simple_report.updated_at == timezone.now()

    def test_udpated_at_is_changed_on_new_saves(self, simple_report, freezer):
        new_date = timezone.now() + timedelta(days=10)
        freezer.move_to(new_date)

        simple_report.save()

        assert simple_report.updated_at == new_date

    def test_published_default_value(self, simple_report):
        assert not simple_report.published

    def test_notes_can_be_null(self, factory_cls):
        factory_cls(notes=None)

    def test_tags_are_empty_by_default(self, simple_report):
        assert simple_report.tags.count() == 0

    def test_ordering_shows_newest_first(self, factory_cls):
        t = timezone.now()
        old = factory_cls(created_at=t)
        oldest = factory_cls(created_at=t - timedelta(seconds=10))
        newest = factory_cls(created_at=t + timedelta(seconds=10))

        assert frozenset(list(factory_cls._meta.model.objects.all())) == frozenset([oldest, old, newest])

    def test__str__(self, simple_report):
        assert simple_report.__str__() == f"{simple_report.__class__.__name__} ({simple_report.uuid})"


class BaseTestReversionedReport:
    def test_report_is_versioned_in_create(self, factory_cls):
        with create_revision():
            obj = factory_cls()

        assert Version.objects.get_for_object(obj).count() == 1

    def test_report_is_versioned_in_update(self, factory_cls):
        with create_revision():
            obj = factory_cls(notes="v1")

        with create_revision():
            obj.notes = "v2"
            obj.save()

        assert Version.objects.get_for_object(obj)[0].field_dict["notes"] == "v2"
        assert Version.objects.get_for_object(obj)[1].field_dict["notes"] == "v1"

    def test_report_version_deletions(self, factory_cls):
        with create_revision():
            obj = factory_cls()

        obj.delete()

        assert Version.objects.get_deleted(obj.__class__).count() == 1

    def test_report_can_be_reverted(self, factory_cls):
        with create_revision():
            obj = factory_cls(notes="v1")

        with create_revision():
            obj.notes = "v2"
            obj.save()

        Version.objects.get_for_object(obj)[1].revision.revert()

        obj.refresh_from_db()

        assert obj.notes == "v1"


class TestBiteReport(BaseTestReversionedReport, TestReport):
    @pytest.fixture
    def factory_cls(self):
        return BiteReportFactory

    # Tests override
    def test_published_default_value(self, simple_report):
        assert simple_report.published

    # Custom tests


class TestBreedingSiteReport(BaseTestReversionedReport, TestReport):
    @pytest.fixture
    def factory_cls(self):
        return BreedingSiteReportFactory

    # Tests override
    def test_published_default_value(self, simple_report):
        assert simple_report.published

    # Custom tests
    def test_breeding_site_can_init_blank(self, factory_cls):
        factory_cls(breeding_site=None)

    def test_breeding_site_can_not_be_null(self, factory_cls):
        report = factory_cls(breeding_site=None)

        report.breeding_site = None

        with pytest.raises(IntegrityError, match=r"violates not-null constraint"):
            report.save()

    def test_has_water_is_mandatory(self, factory_cls):
        with pytest.raises(IntegrityError, match=r"violates not-null constraint"):
            factory_cls(has_water=None)

    def test_breeding_site_is_preseved_if_not_init_None(self, factory_cls):
        b_s = BreedingSiteFactory()
        report = factory_cls(breeding_site=b_s)

        assert report.breeding_site == b_s

    def test_breeding_site_blank_creates_new_breeding_site_if_not_near_found(self, factory_cls):
        assert BreedingSite.objects.all().count() == 0
        report = factory_cls(breeding_site=None)

        assert report.breeding_site is not None
        assert BreedingSite.objects.all().count() == 1

    @pytest.mark.parametrize(
        "point",
        [Point(x=random.uniform(-180, 180), y=float(lat), srid=4326) for lat in range(-90, 90, 5)],
    )
    def test_breeding_site_blank_sets_nearest_object_in_50meters(self, factory_cls, point):
        BreedingSiteFactory(point=create_random_point_at_distance(center_point=point, distance_meters=100))
        nearest_b_s = BreedingSiteFactory(
            point=create_random_point_at_distance(center_point=point, distance_meters=20)
        )
        BreedingSiteFactory(point=create_random_point_at_distance(center_point=point, distance_meters=40))

        report = factory_cls(point=point, breeding_site=None)

        assert report.breeding_site == nearest_b_s

    @pytest.mark.parametrize(
        "point",
        [Point(x=random.uniform(-180, 180), y=float(lat), srid=4326) for lat in range(-90, 90, 5)],
    )
    def test_breeding_site_blank_creates_new_if_no_near_objects_found_in_50meteres(self, factory_cls, point):
        far_b_s = BreedingSiteFactory(point=create_random_point_at_distance(center_point=point, distance_meters=100))

        report = factory_cls(point=point, breeding_site=None)

        assert report.breeding_site is not None
        assert report.breeding_site != far_b_s


class TestIndividualReport(BaseTestReversionedReport, TestReport):
    @pytest.fixture
    def factory_cls(self):
        return IndividualReportFactory

    # Custom tests
    def test_individual_can_be_blank(self, factory_cls):
        factory_cls(individual=None)

    def test_inidividual_is_auto_created_if_blank(self, factory_cls):
        report = factory_cls(individual=None)

        assert report.individual is not None

    def test_individual_is_kept_if_defined(self, factory_cls):
        i = IndividualFactory()
        report = factory_cls(individual=i)

        assert report.individual == i

    def test_individual_can_not_be_set_to_None(self, factory_cls):
        report = factory_cls()

        report.individual = None

        with pytest.raises(IntegrityError, match=r"violates not-null constraint"):
            report.save()

    def test_individual_deletion_is_cascaded(self, factory_cls):
        i = IndividualFactory()
        report = factory_cls(individual=i)

        i.delete()

        assert IndividualReport.objects.filter(pk=report.pk).count() == 0

    def test_taxon_can_be_None(self, factory_cls):
        factory_cls(taxon=None)

    def test_taxon_deletion_is_protected(self, factory_cls, taxon_specie):
        factory_cls(taxon=taxon_specie)

        with pytest.raises(ProtectedError):
            taxon_specie.delete()
