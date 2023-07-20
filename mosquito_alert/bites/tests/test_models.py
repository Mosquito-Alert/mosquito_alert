import pytest
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.utils import timezone

from mosquito_alert.individuals.tests.factories import IndividualFactory

from ..models import Bite
from .factories import BiteFactory


@pytest.mark.django_db
class TestBiteModel:
    def test_bite_is_protected_on_individual_delete(self):
        individual = IndividualFactory()
        _ = BiteFactory(individual=individual)

        with pytest.raises(ProtectedError):
            individual.delete()

    def test_bite_allow_null_individual(self):
        _ = BiteFactory(individual=None)

    def test_do_not_allow_null_bodypart(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            _ = BiteFactory(body_part=None)

    def test_auto_datetime(self, freezer):
        # freezer is fixture from pytest-freezegun
        bite = BiteFactory()
        assert bite.datetime == timezone.now()

    def test__str__(self, freezer):
        # freezer is fixture from pytest-freezegun
        bite = BiteFactory(body_part=Bite.BodyParts.HEAD)
        expected_str = "{} ({})".format(Bite.BodyParts.HEAD.label, timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
        assert bite.__str__() == expected_str
