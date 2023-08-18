from abc import ABC, abstractmethod
from contextlib import nullcontext as does_not_raise
from datetime import timedelta

import pytest
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.timesince import timesince

from .models import (
    DummyAL_NodeParentManageableModel,
    DummyMP_NodeExpandedQueriesModel,
    DummyMP_NodeParentManageableModel,
    DummyNonNodeParentManageableModel,
    DummyNS_NodeParentManageableModel,
    DummyTimeStampedModel,
)


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

    def test_get_num_children_is_0_on_single_root_node(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()

        assert root_node.get_num_children() == 0

    def test_has_children_is_False_on_single_root_node(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()

        assert root_node.has_children() is False

    def test_get_num_children_is_on_tree(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()
        root_node.add_child()

        assert root_node.get_num_children() == 1

    def test_has_children_is_True_on_tree(self):
        root_node = DummyMP_NodeExpandedQueriesModel.add_root()
        root_node.add_child()

        assert root_node.has_children() is True


@pytest.mark.django_db
class BaseTestTimeStampedModel(ABC):
    @property
    @abstractmethod
    def model(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def factory_cls(self):
        raise NotImplementedError

    # Fields
    @pytest.mark.freeze_time
    def test_created_at_default_is_now(self):
        obj = self.factory_cls()

        assert obj.created_at == timezone.now()

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
        obj = self.factory_cls()

        yesterday = timezone.now() - timedelta(days=1)
        obj.created_at = yesterday
        obj.save()

        assert obj.created_at == yesterday
        assert obj.updated_at == timezone.now()

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
        obj = self.model()
        different_date = timezone.now() - timedelta(weeks=52)
        obj.created_at = different_date
        obj.updated_at = different_date
        obj.save()

        assert obj.created_at == different_date
        assert obj.updated_at == different_date

        different_date2 = timezone.now() - timedelta(weeks=26)
        obj.created_at = different_date2
        obj.updated_at = different_date2
        obj.save()

        assert obj.created_at == different_date2
        assert obj.updated_at != different_date2
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
    factory_cls = DummyTimeStampedModel.objects.create
