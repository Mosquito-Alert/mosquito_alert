from abc import ABC
from unittest.mock import PropertyMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone

from mosquito_alert.users.tests.factories import UserFactory
from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin, BaseTestTimeStampedModel

from ..models import Flag, FlagInstance, FlagModeratedModel
from .factories import DummyFlagModeratedModelFactory, DummyModelFactory, FlagFactory, FlagInstanceFactory
from .testapp.models import DummyFlagModeratedModel


def test_FlagModeratedModel_is_abstract():
    assert FlagModeratedModel._meta.abstract


@pytest.mark.django_db
class TestFlag(BaseTestTimeStampedModel):
    model = Flag
    factory_cls = FlagFactory

    # fields
    def test_content_type_can_not_be_null(self):
        assert not self.model._meta.get_field("content_type").null

    def test_content_type_on_delete_is_cascade(self):
        assert self.model._meta.get_field("content_type").remote_field.on_delete == models.CASCADE

    def test_object_id_can_not_be_null(self):
        assert not self.model._meta.get_field("object_id").null

    def test_moderator_can_be_null(self):
        assert self.model._meta.get_field("moderator").null

    def test_moderator_can_be_blank(self):
        assert self.model._meta.get_field("moderator").blank

    def test_moderator_on_delete_is_setnull(self):
        assert self.model._meta.get_field("moderator").remote_field.on_delete == models.SET_NULL

    def test_moderator_related_name(self):
        assert self.model._meta.get_field("moderator").remote_field.related_name == "flags_moderated"

    def test_is_active_can_not_be_null(self):
        assert not self.model._meta.get_field("is_active").null

    def test_is_active_is_default_False(self):
        assert self.model._meta.get_field("is_active").default is False

    def test_count_can_not_be_null(self):
        assert not self.model._meta.get_field("count").null

    def test_count_is_default_0(self):
        assert self.model._meta.get_field("count").default == 0

    def test_count_is_not_editable(self):
        assert not self.model._meta.get_field("count").editable

    def test_moderated_at_can_be_null(self):
        assert self.model._meta.get_field("moderated_at").null

    def test_moderated_at_can_be_blank(self):
        assert self.model._meta.get_field("moderated_at").blank

    def test_moderated_at_is_not_editable(self):
        assert not self.model._meta.get_field("moderated_at").editable

    # object manager
    def test_objects_active_returns_only_active_flags(self):
        obj_active = self.factory_cls(is_active=True)
        obj_not_active = self.factory_cls(is_active=False)

        assert list(self.model.objects.active()) == [obj_active]
        assert list(self.model.objects.active(False)) == [obj_not_active]

    def test_objects_moderated_returns_moderatet_at_is_not_null(self):
        obj_moderated = self.factory_cls(moderated_at=timezone.now())
        obj_not_moderated = self.factory_cls(moderated_at=None)

        assert list(self.model.objects.moderated()) == [obj_moderated]
        assert list(self.model.objects.moderated(False)) == [obj_not_moderated]

    # properties
    @pytest.mark.parametrize("moderated_at, expected_result", [(None, False), (object(), True)])
    def test_has_been_reviewed(self, moderated_at, expected_result):
        assert self.factory_cls.build(moderated_at=moderated_at).has_been_reviewed == expected_result

    def test_increase_count_add_1_to_count(self):
        obj = self.factory_cls(count=10)

        obj.increase_count()

        assert obj.count == 11

    @patch(f"{model.__module__}.update_object_counter")
    def test_increase_count_use_update_objects_counter_function(self, mocked_func):
        obj = self.factory_cls()

        obj.increase_count()

        mocked_func.assert_called_once_with(obj=obj, fieldname="count", inc_value=1)

    @patch(f"{model.__module__}.{model.__name__}.has_been_reviewed", new_callable=PropertyMock)
    def test_increase_count_sets_moderated_at_to_None_if_not_active_and_has_been_reviewed(
        self, mocked_has_been_reviewed
    ):
        obj = self.factory_cls()

        mocked_has_been_reviewed.return_value = True
        obj.is_active = False

        obj.increase_count()

        assert obj.moderated_at is None

    @patch(f"{model.__module__}.{model.__name__}.has_been_reviewed", new_callable=PropertyMock)
    def test_increase_count_sets_moderator_to_None_if_not_active_and_has_been_reviewed(self, mocked_has_been_reviewed):
        obj = self.factory_cls()

        mocked_has_been_reviewed.return_value = True
        obj.is_active = False

        obj.increase_count()

        assert obj.moderator is None

    def test_decrease_count_subtract_1_to_count(self):
        obj = self.factory_cls(count=10)

        obj.decrease_count()

        assert obj.count == 9

    @patch(f"{model.__module__}.update_object_counter")
    def test_decrease_count_use_update_objects_counter_function(self, mocked_func):
        obj = self.factory_cls(count=1)
        obj.decrease_count()

        mocked_func.assert_called_once_with(obj=obj, fieldname="count", inc_value=-1)

    # meta
    def test_unique_by_content_object(self):
        dummy_object = self.factory_cls()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, content_object=dummy_object)


@pytest.mark.django_db
class TestFlagInstance(BaseTestTimeStampedModel):
    model = FlagInstance
    factory_cls = FlagInstanceFactory

    # fields
    def test_user_can_be_null(self):
        assert self.model._meta.get_field("user").null

    def test_user_can_be_blank(self):
        assert self.model._meta.get_field("user").blank

    def test_user_on_delete_is_setnull(self):
        assert self.model._meta.get_field("user").remote_field.on_delete == models.SET_NULL

    def test_user_related_name(self):
        assert self.model._meta.get_field("user").remote_field.related_name == "created_flags"

    def test_flag_can_not_be_null(self):
        assert not self.model._meta.get_field("flag").null

    def test_flag_on_delete_is_cascade(self):
        assert self.model._meta.get_field("flag").remote_field.on_delete == models.CASCADE

    def test_flag_related_name(self):
        assert self.model._meta.get_field("flag").remote_field.related_name == "flags"

    def test_reason_can_not_be_null(self):
        assert not self.model._meta.get_field("reason").null

    def test_notes_can_be_null(self):
        assert self.model._meta.get_field("notes").null

    def test_notes_can_be_blank(self):
        assert self.model._meta.get_field("notes").blank

    # objects
    def test_objects_create_accepts_model_obj(self):
        obj_dummy = DummyModelFactory()

        obj = self.model.objects.create(model_obj=obj_dummy, reason=FlagInstance.Reason.ABUSIVE)

        assert obj.flag.content_object == obj_dummy

    # methods
    def test_clean_raises_if_reason_is_OTHER_and_empty_notes(self):
        obj = self.factory_cls.build(reason=FlagInstance.Reason.OTHER, notes=None)

        with pytest.raises(ValidationError):
            obj.clean()

    def test_save_calls_clean(self):
        obj = self.factory_cls.build(flag=FlagFactory())

        with patch.object(obj, "clean") as mocked_clean:
            obj.save()

            mocked_clean.assert_called_once()

    def test_save_calls_increase_count_on_flag_on_create(self):
        obj = self.factory_cls.build(flag=FlagFactory())

        with patch.object(obj.flag, "increase_count") as mocked_method:
            obj.save()

            mocked_method.assert_called_once()

        with patch.object(obj.flag, "increase_count") as mocked_method:
            obj.save()

            mocked_method.assert_not_called()

    def test_flag_counter_increase_after_create(self):
        obj_flag = FlagFactory(count=1)
        obj = self.factory_cls(flag=obj_flag)

        assert obj.flag.count == 2

    def test_delete_calls_decrease_count(self):
        obj = self.factory_cls()

        with patch.object(obj.flag, "decrease_count") as mocked_method:
            obj.delete()

            mocked_method.assert_called_once()

    def test_flag_counter_decrease_after_delete(self):
        obj_flag = FlagFactory(count=10)
        obj = self.factory_cls(flag=obj_flag)

        obj.delete()

        assert obj.flag.count == 10

    # meta
    def test_constraint_unique_flag_by_user_only_if_user_is_not_null(self):
        flag = FlagFactory()

        # Case user is null -> NOT RAISE
        _ = self.factory_cls.create_batch(size=2, flag=flag, user=None)

        # Case user is not null -> RAISE
        user = UserFactory()
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            self.factory_cls.create_batch(size=2, flag=flag, user=user)


@pytest.mark.django_db
class BaseTestFlagModeratedModel(AbstractDjangoModelTestMixin, ABC):
    # fields
    def test_flags_field_exist(self):
        assert self.model._meta.get_field("flags")

    # objects
    def test_objects_flagged(self):
        obj_flagged = self.factory_cls(flags=[FlagFactory(is_active=True)])
        obj_not_flagged = self.factory_cls(flags=[FlagFactory(is_active=False)])
        obj_empty = self.factory_cls()

        assert list(self.model.objects.flagged()) == [obj_flagged]
        assert frozenset(self.model.objects.flagged(False)) == frozenset([obj_not_flagged, obj_empty])

    # properties
    def test_is_flagged_is_true_if_flag_is_active(self):
        assert self.factory_cls(flags=[FlagFactory(is_active=True)]).is_flagged
        assert not self.factory_cls(flags=[FlagFactory(is_active=False)]).is_flagged


@pytest.mark.django_db
class TestFlagModeratedModel(BaseTestFlagModeratedModel):
    model = DummyFlagModeratedModel
    factory_cls = DummyFlagModeratedModelFactory
