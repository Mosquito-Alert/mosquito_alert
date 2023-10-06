import random

import factory
import factory.fuzzy
from factory.django import DjangoModelFactory

from mosquito_alert.images.tests.factories import PhotoFactory

from ..models import BaseShape


class BaseTaskFactory(DjangoModelFactory):
    class Meta:
        abstract = True


class BaseAnnotationTaskFactory(BaseTaskFactory):
    class Meta:
        abstract = True


class BasePhotoAnnotationTaskFactory(BaseAnnotationTaskFactory):
    photo = factory.SubFactory(PhotoFactory)

    class Meta:
        abstract = True


class BaseAnnotationFactory(DjangoModelFactory):
    class Meta:
        abstract = True


class BasePhotoAnnotationFactory(BaseAnnotationFactory):
    class Meta:
        abstract = True


class FuzzyRectangle(factory.fuzzy.BaseFuzzyAttribute):
    """Yields random rectangle"""

    def fuzz(self):
        top_left = [random.uniform(0, 1), random.uniform(0, 1)]
        bottom_right = [random.uniform(top_left[0], 1), random.uniform(top_left[1], 1)]

        return [top_left, bottom_right]


class BaseShapeFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    class Params:
        is_rectangular = factory.Trait(shape_type=BaseShape.ShapeType.RECTANGLE, points=FuzzyRectangle())


class RectangularShapeFactory(DjangoModelFactory):
    shape_type = BaseShape.ShapeType.RECTANGLE
    points = FuzzyRectangle()

    class Meta:
        abstract = True
