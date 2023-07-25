import pytest
from django.db.utils import IntegrityError
from flag.models import Flag

from ..models import FlagModeratedModel
from .factories import DummyFlagModeratedModelFactory, FlagFactory


@pytest.mark.django_db
class TestFlagModeratedModel:
    def test_model_is_abstract(self):
        assert FlagModeratedModel._meta.abstract

    def test_flags_field_exist(self):
        FlagModeratedModel._meta.get_field("flags")

    def test_only_one_flag_is_allowed(self):
        obj = DummyFlagModeratedModelFactory(flags=None)

        _ = FlagFactory(content_object=obj)

        with pytest.raises(IntegrityError, match=r"violates unique constraint"):
            _ = FlagFactory(content_object=obj)

    @pytest.mark.parametrize("value", [Flag.State.FLAGGED.value, Flag.State.NOTIFIED.value])
    def test_is_banned_states(self, value):
        assert value in FlagModeratedModel.IS_BANNED_STATES

    def test_prop_is_permitted_when_empty_flags(self):
        obj = DummyFlagModeratedModelFactory(flags=None)

        assert not obj.flags.exists()

        assert obj.is_permitted
        assert not obj.is_banned

    @pytest.mark.parametrize("state_value", set(Flag.State) - set(FlagModeratedModel.IS_BANNED_STATES))
    def test_prop_is_permitted_with_non_banned_state(self, state_value):
        obj = DummyFlagModeratedModelFactory(flags__state=state_value)

        assert obj.is_permitted
        assert not obj.is_banned

    @pytest.mark.parametrize("state_value", FlagModeratedModel.IS_BANNED_STATES)
    def test_prop_is_banned_with_banned_state(self, state_value):
        obj = DummyFlagModeratedModelFactory(flags__state=state_value)

        assert obj.is_banned
        assert not obj.is_permitted
