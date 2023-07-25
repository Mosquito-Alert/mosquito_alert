import pytest

from .factories import DummyFlagModeratedModelFactory
from .testapp.models import DummyFlagModeratedModel


@pytest.mark.django_db
class TestFlagModeratedManager:
    @pytest.fixture
    def banned_obj(self):
        return DummyFlagModeratedModelFactory(is_banned=True)

    @pytest.fixture
    def permitted_obj(self):
        return DummyFlagModeratedModelFactory(is_permitted=True)

    @pytest.fixture
    def empty_flag_obj(self):
        return DummyFlagModeratedModelFactory(flags=None)

    def test_with_banned_state(self, banned_obj, permitted_obj, empty_flag_obj):
        qs = DummyFlagModeratedModel.objects.with_banned_state()

        assert frozenset(qs.all()) == frozenset([banned_obj])

    def test_with_permitted_state(self, banned_obj, permitted_obj, empty_flag_obj):
        qs = DummyFlagModeratedModel.objects.with_permitted_state()

        assert frozenset(qs.all()) == frozenset([permitted_obj, empty_flag_obj])
