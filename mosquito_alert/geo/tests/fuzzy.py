from django.contrib.gis.geos import MultiPolygon, Point, Polygon

import factory.fuzzy
from factory import random
from faker import Faker
from random import uniform


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
            length = random.randgen.randrange(3, 6, 1)
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


class FuzzyGriddedPolygon(factory.fuzzy.BaseFuzzyAttribute):
    _counter = 0  # shared across instances

    def __init__(self, srid=None, cell_size=1.0, jitter=0.2, **kwargs):
        self.srid = srid
        self.cell_size = cell_size
        self.jitter = jitter
        super().__init__(**kwargs)

    @classmethod
    def _next_cell(cls):
        n = cls._counter
        cls._counter += 1
        return n

    def fuzz(self):
        n = self._next_cell()

        # grid position
        cols = 10  # adjust grid width
        x = (n % cols) * self.cell_size
        y = (n // cols) * self.cell_size

        # jitter to avoid identical squares
        j = self.jitter
        dx = uniform(0, j)
        dy = uniform(0, j)

        poly = Polygon(
            [
                (x + dx, y + dy),
                (x + self.cell_size - dx, y + dy),
                (x + self.cell_size - dx, y + self.cell_size - dy),
                (x + dx, y + self.cell_size - dy),
                (x + dx, y + dy),
            ],
            srid=self.srid,
        )

        return poly


class FuzzyMultiPolygon(factory.fuzzy.BaseFuzzyAttribute):
    """Yields random multipolygon"""

    def __init__(self, srid=None, length=None, polygon_klass=FuzzyPolygon, **kwargs):
        if length is None:
            length = random.randgen.randrange(2, 3, 1)
        if length < 2:
            raise Exception("MultiPolygon needs to be 2 or greater in length.")
        self.length = length
        self.srid = srid
        self.polygon_klass = polygon_klass
        super().__init__(**kwargs)

    def fuzz(self):
        polygons = [
            self.polygon_klass(srid=self.srid).fuzz() for __ in range(self.length)
        ]
        return MultiPolygon(*polygons, srid=self.srid)
