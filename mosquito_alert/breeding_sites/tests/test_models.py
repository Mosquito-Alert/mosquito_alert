import pytest

from .factories import BreedingSiteFactory


@pytest.mark.django_db
class TestBreedingSiteModel:
    def test_allow_null_type(self):
        _ = BreedingSiteFactory(type=None)

    def test__str__with_location_type(self):
        obj = BreedingSiteFactory()
        loc = obj.location
        point = loc.point

        expected_output = (
            f"{obj.get_type_display()} ({point.coords} ({loc.location_type}))"
        )
        assert obj.__str__() == expected_output

    def test__str__without_location_type(self):
        obj = BreedingSiteFactory(location__location_type=None)
        loc = obj.location
        point = loc.point

        expected_output = f"{obj.get_type_display()} ({point.coords})"
        assert obj.__str__() == expected_output
