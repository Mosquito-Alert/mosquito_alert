import pytest

from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin

from ..models import BreedingSite
from .factories import BreedingSiteFactory


@pytest.mark.django_db
class TestBreedingSiteModel(AbstractDjangoModelTestMixin):
    model = BreedingSite
    factory_cls = BreedingSiteFactory

    # fields
    def test_type_can_be_null(self):
        assert self.model._meta.get_field("type").null

    def test_type_can_be_blank(self):
        assert self.model._meta.get_field("type").blank

    # meta
    def test__str__with_location_type(self):
        obj = BreedingSiteFactory()
        loc = obj.location
        point = loc.point

        expected_output = f"{obj.get_type_display()} ({point.coords} ({loc.location_type}))"
        assert obj.__str__() == expected_output

    def test__str__without_location_type(self):
        obj = BreedingSiteFactory(location__location_type=None)
        loc = obj.location
        point = loc.point

        expected_output = f"{obj.get_type_display()} ({point.coords})"
        assert obj.__str__() == expected_output
