
from datetime import timedelta
import time_machine
import uuid

from django.contrib.gis.geos import Polygon, MultiPolygon, Point, LineString
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from mosquito_alert.geo.models import TemporaryBoundary


@override_settings(CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-test-cache",
        }
    })
class TemporaryBoundaryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.polygon = Polygon.from_bbox((0.0, 0.0, 1.0, 1.0))
        cls.multipolygon = MultiPolygon(cls.polygon)
        cls.point = Point(0.0, 0.0)
        cls.line = LineString([(0.0, 0.0), (1.0, 1.0)])

    def test_accepts_valid_geometries(self):
        for geom in [self.polygon, self.multipolygon]:
            boundary = TemporaryBoundary(geometry=geom)
            boundary.save()
            self.assertEqual(boundary.geometry, geom)
            self.assertIsInstance(boundary.uuid, uuid.UUID)

    def test_rejects_invalid_geometries(self):
        for geom in [self.point, self.line]:
            with self.assertRaises(ValueError):
                TemporaryBoundary(geometry=geom)

    def test_save_stores_geometry_in_cache(self):
        boundary = TemporaryBoundary(geometry=self.polygon)
        boundary.save()
        cached_wkt = cache.get(str(boundary.uuid))
        self.assertEqual(cached_wkt, self.polygon.wkt)

    def test_create_temporary_boundary_expires(self):
        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            boundary = TemporaryBoundary(geometry=self.polygon)
            boundary.save()

            traveller.shift(timedelta(seconds=boundary.expires_in-1))
            self.assertIsNotNone(TemporaryBoundary.get(boundary.uuid))
            traveller.shift(timedelta(seconds=1))
            with self.assertRaises(ValueError):
                TemporaryBoundary.get(boundary.uuid)

    @time_machine.travel("2024-01-01 00:00:00", tick=False)
    def test_expires_in_returns_correct_seconds(self):
        boundary = TemporaryBoundary(geometry=self.polygon)
        boundary.expires_at = timezone.now() + timedelta(seconds=30)

        self.assertEqual(boundary.expires_in, 30)

        # Check it never returns negative
        boundary.expires_at = timezone.now() - timedelta(seconds=10)
        self.assertEqual(boundary.expires_in, 0)

    def test_get_returns_saved_boundary(self):
        boundary = TemporaryBoundary(geometry=self.polygon)
        boundary.save()

        retrieved_boundary = TemporaryBoundary.get(boundary.uuid)

        self.assertEqual(retrieved_boundary.uuid, boundary.uuid)
        self.assertEqual(retrieved_boundary.geometry, self.polygon)

    def test_get_raises_error_if_not_cached(self):
        with self.assertRaises(ValueError):
            TemporaryBoundary.get(uuid.uuid4())
