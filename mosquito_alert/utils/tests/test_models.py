from abc import ABC, abstractmethod
from contextlib import nullcontext as does_not_raise
from datetime import timedelta
from unittest.mock import Mock, call, patch

import pytest
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.timesince import timesince

from .factories import DummyObservableModelFactory, DummyTimeStampedModelFactory
from .models import (
    DummyAL_NodeParentManageableModel,
    DummyMP_NodeExpandedQueriesModel,
    DummyMP_NodeParentManageableModel,
    DummyNonNodeParentManageableModel,
    DummyNS_NodeParentManageableModel,
    DummyObservableModel,
    DummyTimeStampedModel,
)


class AbstractDjangoModelTestMixin(ABC):
    @property
    @abstractmethod
    def model(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def factory_cls(self):
        raise NotImplementedError


class TestUniqueParentManageableNodeMixin:
    def test_non_node_model_inherits_parent_manageable_node_mixin(self):
        with pytest.raises(NotImplementedError):
            DummyNonNodeParentManageableModel.objects.create(pk=1)

    @pytest.mark.parametrize(
        "klass, expected_output, expected_raise",
        [
            (DummyMP_NodeParentManageableModel, "path", does_not_raise()),
            (
                DummyAL_NodeParentManageableModel,
                None,
                pytest.raises(NotImplementedError),
            ),
            (DummyNS_NodeParentManageableModel, "lft", does_not_raise()),
            (
                DummyNonNodeParentManageableModel,
                None,
                pytest.raises(NotImplementedError),
            ),
        ],
    )
    def test_get_mandatory_field_func(self, klass, expected_output, expected_raise):
        with expected_raise:
            assert klass()._get_mandatory_field() == expected_output


@pytest.mark.django_db
@pytest.mark.parametrize("model_cls", [DummyMP_NodeParentManageableModel, DummyNS_NodeParentManageableModel])
class TestParentManageableNodeMixin:
    def test_parent_property_return_None_on_parent_nodes(self, model_cls):
        node1 = model_cls.add_root()

        assert node1.parent is None

    def test_parent_property_return_parent_on_child_nodes(self, model_cls):
        parent_node = model_cls.add_root()
        child_node = parent_node.add_child()

        assert child_node.parent == parent_node

    def test_parent_property_changes_on_parent_update(self, model_cls):
        parent_node = model_cls.add_root()
        child_node = parent_node.add_child()

        parent_node1 = model_cls.add_root()

        child_node.parent = parent_node1
        # Pre save
        assert child_node.parent == parent_node1

        child_node.save()
        # Post save
        assert child_node.parent == parent_node1

        # Parent set to None
        child_node.parent = None
        child_node.save()
        assert child_node.parent is None

    def test_node_is_set_to_root_on_parent_set_to_None(self, model_cls):
        parent_node = model_cls.add_root()
        child_node = parent_node.add_child()

        child_node.parent = None
        child_node.save()

        assert child_node.is_root()

    def test_create_root_when_parent_not_set_on_calling_create_method(self, model_cls):
        node = model_cls.objects.create()
        assert node.parent is None
        assert node.is_root()

    def test_create_root_when_parent_set_None_on_calling_create_method(self, model_cls):
        node = model_cls.objects.create(parent=None)
        assert node.parent is None
        assert node.is_root()

    def test_create_children_calling_create_method(self, model_cls):
        parent_node = model_cls.objects.create()
        children_node = model_cls.objects.create(parent=parent_node)
        assert children_node.parent == parent_node

    def test_create_root_if_parent_not_set_on__init__(self, model_cls):
        node = model_cls()
        node.save()

        assert node.parent is None
        assert node.is_root()

    def test_parent_argument_on__init__(self, model_cls):
        parent_node = model_cls.objects.create()
        node = model_cls(parent=parent_node)
        node.save()

        assert node.parent == parent_node

    def test_move_node_on_parent_update(self, model_cls):
        parent_node = model_cls.objects.create()
        node = model_cls.objects.create(parent=parent_node)
        node1 = model_cls.objects.create(parent=node)

        assert node1.parent == node
        assert node1.is_leaf() is True
        assert node1.get_depth() == 3

        # Change parent
        node1.parent = parent_node
        node1.save()

        parent_node.refresh_from_db()
        node.refresh_from_db()

        # Test node1 parent has changed
        assert node1.parent == parent_node

        # Test node1 get_depth has changed
        assert node1.get_depth() == 2

        # Test node1 get_ancestors return parent
        assert list(node1.get_ancestors()) == [parent_node]

        # Test node1 get_root return parent
        assert node1.get_root() == parent_node

        # Test node1 get_siblings return parent
        assert list(node1.get_siblings()) == [node1, node]

        # Test node1 is_sibling_of node return True
        assert node1.is_sibling_of(node) is True

        # Test node1 is_child_of parent return True
        assert node1.is_child_of(parent_node) is True

        # Test node1 is_descendant_of parent return True
        assert node1.is_descendant_of(parent_node) is True

        # Test node1 is_leaf() return True
        assert node1.is_leaf() is True

        # Test parent get_children return new nodes
        assert list(parent_node.get_children()) == [node1, node]

        # Test parent get_children_count return 2
        assert parent_node.get_children_count() == 2

        # Test parent get_descendants return new node
        assert list(parent_node.get_descendants()) == [node1, node]

        # Test parent get_descendant_count() return 2
        assert parent_node.get_descendant_count() == 2

        # Test node get_siblings() return node1
        assert list(node.get_siblings()) == [node1, node]

        # Test node is_sibling_of node1 return True
        assert node.is_sibling_of(node1) is True

        # Test node is_leaf() return True
        assert node.is_leaf() is True

        assert node.get_children_count() == 0

    def test_should_send_signal_on_parent_change(self, model_cls, mocker):
        m = mocker.patch("mosquito_alert.utils.models.parent_has_changed.send")

        parent_node = model_cls.objects.create()
        node = model_cls.objects.create(parent=parent_node)
        node1 = model_cls.objects.create(parent=node)

        # Change parent
        node1.parent = parent_node
        node1.save()

        m.assert_called_once_with(sender=model_cls, instance=node1)

    def test_should_send_signal_on_parent_change_set_to_None(self, model_cls, mocker):
        m = mocker.patch("mosquito_alert.utils.models.parent_has_changed.send")

        parent_node = model_cls.objects.create()
        node = model_cls.objects.create(parent=parent_node)

        # Change parent
        node.parent = None
        node.save()

        m.assert_called_once_with(sender=model_cls, instance=node)

    def test_should_not_send_signal_on_save(self, model_cls, mocker):
        m = mocker.patch("mosquito_alert.utils.models.parent_has_changed.send")

        parent_node = model_cls.objects.create()
        node = model_cls.objects.create(parent=parent_node)

        # Parent is set but not changed
        node.parent = parent_node
        node.save()

        m.assert_not_called()


@pytest.mark.django_db
class TestNodeExpandedQueriesMixin:
    def test_get_ancestors_and_self_if_root(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()

        assert root_node.get_ancestors_and_self() == [root_node]

    def test_get_ancestors_and_self_in_tree(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()
        child_node = root_node.add_child()

        assert list(child_node.get_ancestors_and_self()) == [root_node, child_node]

    def test_get_descendants_and_self(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()
        child_node = root_node.add_child()

        assert list(root_node.get_descendants_and_self()) == [root_node, child_node]


@pytest.mark.django_db
class BaseTestTimeStampedModel(AbstractDjangoModelTestMixin, ABC):
    # Fields
    @pytest.mark.freeze_time
    def test_created_at_default_is_now(self):
        obj = self.factory_cls()

        assert obj.created_at == timezone.now()

    def test_created_at_can_not_be_null(self):
        assert not self.model._meta.get_field("created_at").null

    def test_created_at_is_not_editable(self):
        assert not self.model._meta.get_field("created_at").editable

    def test_created_at_is_blank(self):
        assert self.model._meta.get_field("created_at").blank

    @pytest.mark.freeze_time
    def test_created_at_can_be_set_manually(self):
        yesterday = timezone.now() - timedelta(days=1)
        obj = self.factory_cls(created_at=yesterday)

        assert obj.created_at == yesterday

    @pytest.mark.freeze_time
    def test_overriding_created_at_after_object_created(self):
        yesterday = timezone.now() - timedelta(days=1)
        obj = self.factory_cls(created_at=yesterday)

        now = timezone.now()
        obj.created_at = now
        obj.save()

        assert obj.created_at == now
        assert obj.updated_at == now

    @pytest.mark.freeze_time
    def test_updated_at_default_is_now(self):
        obj = self.factory_cls()

        assert obj.updated_at == timezone.now()

    def test_updated_at_is_not_editable(self):
        assert not self.model._meta.get_field("updated_at").editable

    def test_updated_at_is_blank(self):
        assert self.model._meta.get_field("updated_at").blank

    @pytest.mark.freeze_time
    def test_updated_at_is_same_as_created_at_if_not_set_on_create(self):
        yesterday = timezone.now() - timedelta(days=1)
        obj = self.factory_cls(created_at=yesterday)

        assert obj.created_at == yesterday
        assert obj.updated_at == yesterday

    @pytest.mark.freeze_time
    def test_values_are_preserved_if_both_set(self):
        yesterday = timezone.now() - timedelta(days=1)
        last_hour = timezone.now() - timedelta(hours=1)

        obj = self.factory_cls(created_at=yesterday, updated_at=last_hour)

        assert obj.created_at == yesterday
        assert obj.updated_at == last_hour

    def test_udpated_at_is_updated_on_save(self, freezer):
        creation_time = timezone.now() - timedelta(days=1)
        freezer.move_to(creation_time)

        obj = self.factory_cls()

        next_hour = timezone.now() + timedelta(hours=1)
        freezer.move_to(next_hour)

        obj.save()

        assert obj.updated_at == next_hour

    def test_overriding_updated_at_after_object_created_does_nothing(self, freezer):
        yesterday = timezone.now() - timedelta(days=1)
        freezer.move_to(yesterday)

        obj = self.factory_cls()

        assert obj.created_at == yesterday
        assert obj.updated_at == yesterday

        last_hour = timezone.now() - timedelta(hours=1)
        obj.updated_at = last_hour
        obj.save()

        assert obj.created_at == yesterday
        assert obj.updated_at != last_hour
        assert obj.updated_at == timezone.now()

    # properties
    def test_created_ago(self):
        obj = self.factory_cls()

        assert obj.created_ago == timesince(obj.created_at)

    def test_updated_ago(self):
        obj = self.factory_cls()

        assert obj.updated_ago == timesince(obj.updated_at)

    # methods
    @pytest.mark.freeze_time
    def test_overrides_using_save(self):
        """
        The first time an object is saved, allow modification of both
        created and updated_at fields.
        After that, only created_at may be modified manually.
        """
        created_at = timezone.now() - timedelta(weeks=52)
        obj = self.factory_cls(created_at=created_at, updated_at=created_at)

        assert obj.created_at == created_at
        assert obj.updated_at == created_at

        two_hours_ago = timezone.now() - timedelta(hours=2)
        obj.created_at = two_hours_ago
        obj.updated_at = two_hours_ago
        obj.save()

        assert obj.created_at == two_hours_ago
        assert obj.updated_at != two_hours_ago
        assert obj.updated_at == timezone.now()

    @pytest.mark.parametrize(
        "update_fields, updated_at_changed",
        [
            (["updated_at"], True),  # list
            (("updated_at",), True),  # tuple
            ({"updated_at"}, True),  # set
            ([], False),  # list
            ((), False),  # tuple
            (set(), False),  # set
            (None, True),
        ],
    )
    def test_save_with_update_fields_overrides_updated_at(self, freezer, update_fields, updated_at_changed):
        """
        Tests if the save method updated updated_at field
        accordingly when update_fields is used as an argument.
        """
        creation_date = timezone.now() - timedelta(days=10)
        freezer.move_to(creation_date)

        obj = self.factory_cls()

        next_day = timezone.now() + timedelta(days=1)
        freezer.move_to(next_day)

        obj.save(update_fields=update_fields)

        assert obj.updated_at == next_day if updated_at_changed else creation_date

    # Meta
    def test_constraint_created_at_can_not_be_futurible(self):
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            _ = self.factory_cls(created_at=timezone.now() + timedelta(seconds=10))

    def test_constraint_updated_at_can_not_be_futurible(self):
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            _ = self.factory_cls(updated_at=timezone.now() + timedelta(seconds=10))

    @pytest.mark.freeze_time
    def test_updated_at_cannot_be_previous_to_created_at(self):
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            _ = self.factory_cls(created_at=timezone.now(), updated_at=timezone.now() - timedelta(seconds=1))


class TestTimeStampedModel(BaseTestTimeStampedModel):
    model = DummyTimeStampedModel
    factory_cls = DummyTimeStampedModelFactory


@pytest.mark.django_db
class BaseTestObservableMixin(AbstractDjangoModelTestMixin, ABC):
    # methods
    def test__init__skip_notify_changes_default_is_false(self):
        assert not self.factory_cls.build().skip_notify_changes

    @pytest.mark.parametrize("value", [True, False])
    def test__skip_notify_changes_is_keep_after_save(self, value):
        obj = self.factory_cls(skip_notify_changes=value)

        assert obj.skip_notify_changes == value

        obj.skip_notify_changes = not value
        obj.save()

        assert obj.skip_notify_changes == (not value)

    @pytest.mark.parametrize("skip_notify_changes, expected_has_called_notify", [(True, False), (False, True)])
    def test__notify_changes_is_called_after_create(self, skip_notify_changes, expected_has_called_notify):
        manager = Mock()

        obj = self.factory_cls.build(skip_notify_changes=skip_notify_changes)

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
            with patch.object(obj, "_run_hooked_methods", return_value=None):
                with patch("django.db.models.base.Model.save", return_value=None) as mocked_super_save:
                    manager.attach_mock(mocked_method, "mock_notify")
                    manager.attach_mock(mocked_super_save, "mock_super_save")

                    obj.save()

        expected_calls = [call.mock_super_save()]

        if expected_has_called_notify:
            expected_calls.append(call.mock_notify())

        manager.assert_has_calls(calls=expected_calls, any_order=False)

    def test__notify_changes_is_not_called_after_create_if_NOTIFY_ON_CREATE_false(self):
        obj = self.factory_cls.build()
        obj.NOTIFY_ON_CREATE = False

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
            with patch.object(obj, "_run_hooked_methods", return_value=None):
                with patch("django.db.models.base.Model.save", return_value=None):
                    obj.save()

                    mocked_method.assert_not_called()

    @pytest.mark.parametrize(
        "skip_notify_changes, mock_changes, expected_has_calls",
        [(True, True, False), (False, True, True), (True, False, False), (False, False, False)],
    )
    def test__notify_changes_is_only_called_on_save_if_field_changes(
        self, skip_notify_changes, mock_changes, expected_has_calls
    ):
        obj = self.factory_cls(skip_notify_changes=skip_notify_changes)

        with patch.object(obj, "has_changed", return_value=mock_changes):
            with patch.object(obj, "_run_hooked_methods", return_value=None):
                with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
                    obj.save()
                    if expected_has_calls:
                        mocked_method.assert_called_once()
                    else:
                        mocked_method.assert_not_called()

    def assert__notify_changes_is_called_on_field_change(self, fieldname, expected_is_called=True):
        obj = self.factory_cls()

        # Force check changed to True
        with patch.object(obj, "has_changed", side_effect=lambda field_name: field_name is fieldname):
            with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
                with patch("django.db.models.base.Model.save", return_value=None):
                    obj.save()
                    if expected_is_called:
                        mocked_method.assert_called_once_with(fields_changed=[fieldname])
                    else:
                        mocked_method.assert_not_called()

    @pytest.mark.parametrize("skip_notify_changes, expected_has_called_notify", [(True, False), (False, False)])
    def test__notify_changes_is_called_after_delete(self, skip_notify_changes, expected_has_called_notify):
        obj = self.factory_cls(skip_notify_changes=skip_notify_changes)

        manager = Mock()

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
            with patch("django.db.models.base.Model.delete", return_value=None) as mocked_super_delete:
                manager.attach_mock(mocked_method, "mock_notify")
                manager.attach_mock(mocked_super_delete, "mock_super_delete")

                obj.delete()

        expected_calls = [call.mock_super_delete()]

        if expected_has_called_notify:
            expected_calls.append(call.mock_notify())

        manager.assert_has_calls(calls=expected_calls, any_order=False)

    def test__notify_changes_is_not_called_after_delete_if_NOTIFY_ON_DELETE_false(self):
        obj = self.factory_cls()
        obj.NOTIFY_ON_DELETE = False

        with patch.object(obj, "_notify_changes", return_value=None) as mocked_method:
            obj.delete()

            mocked_method.assert_not_called()


class TestObservableModel(BaseTestObservableMixin):
    model = DummyObservableModel
    factory_cls = DummyObservableModelFactory

    def test__notify_changes_is_called_on_name_change(self):
        super().assert__notify_changes_is_called_on_field_change(fieldname="name")

    def test__notify_changes_is_not_called_on_hidden_name_change(self):
        super().assert__notify_changes_is_called_on_field_change(fieldname="hidden_name", expected_is_called=False)