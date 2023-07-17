import factory.fuzzy
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from factory import random
from faker import Faker


class FuzzyPoint(factory.fuzzy.BaseFuzzyAttribute):
    def __init__(self, srid=None, **kwargs):
        self.srid = srid
        super().__init__(**kwargs)

    def fuzz(self):
        return Point(tuple(reversed(Faker().latlng())), srid=self.srid)


class FuzzyPolygon(factory.fuzzy.BaseFuzzyAttribute):
    """Yields random polygon"""

    def __init__(self, srid=None, length=None, **kwargs):
        if length is None:
            length = random.randgen.randrange(3, 20, 1)
        if length < 3:
            raise Exception("Polygon needs to be 3 or greater in length.")
        self.length = length
        self.srid = srid
        super().__init__(**kwargs)

    def get_random_coords(self):
        return tuple(reversed(Faker().latlng()))

    def fuzz(self):
        start = end = self.get_random_coords()
        coords = [self.get_random_coords() for __ in range(self.length - 1)]
        return Polygon([start] + coords + [end], srid=self.srid)


class FuzzyMultiPolygon(factory.fuzzy.BaseFuzzyAttribute):
    """Yields random multipolygon"""

    def __init__(self, srid=None, length=None, **kwargs):
        if length is None:
            length = random.randgen.randrange(2, 20, 1)
        if length < 2:
            raise Exception("MultiPolygon needs to be 2 or greater in length.")
        self.length = length
        self.srid = srid
        super().__init__(**kwargs)

    def fuzz(self):
        polygons = [FuzzyPolygon(srid=self.srid).fuzz() for __ in range(self.length)]
        return MultiPolygon(*polygons, srid=self.srid)
