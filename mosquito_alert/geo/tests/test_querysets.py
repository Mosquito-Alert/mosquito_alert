import pytest
from polymorphic.managers import PolymorphicQuerySet

from ..querysets import (
    GeoLocatedModelQuerySet,
    GeoLocatedPolymorphicModelQuerySet,
    LocationQuerySet,
)


class TestLocationQuerySet:
    def test_field_prefix_is_empty_if_None(self):
        l_qs = LocationQuerySet(field_prefix=None)

        assert l_qs.field_prefix == ""

    def test_field_prefix_is_underscored_if_not_None(self):
        l_qs = LocationQuerySet(field_prefix="my_random_field")

        assert l_qs.field_prefix == "my_random_field__"


@pytest.mark.parametrize(
    "qs_cls", [GeoLocatedModelQuerySet, GeoLocatedPolymorphicModelQuerySet]
)
class TestGeoLocatedModelQuerySet:
    def test_default_field_prefix_is_location(self, qs_cls):
        assert qs_cls().field_prefix == "location__"

    def test_field_prefix_is_set(self, qs_cls):
        g_qs = qs_cls(location_fk_field="my_random_field")

        assert g_qs.field_prefix == "my_random_field__"


class TestGeoLocatedPolymorphicModelQuerySet:
    def test_is_subclass_of_polymorhpic(self):
        assert issubclass(GeoLocatedPolymorphicModelQuerySet, PolymorphicQuerySet)
