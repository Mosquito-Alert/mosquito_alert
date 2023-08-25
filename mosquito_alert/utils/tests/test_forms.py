import pytest
from treebeard.forms import movenodeform_factory

from ..forms import AllowOnlyNodesFromSameTreeForm
from .models import DummyMPModel


def reload_dummy_node(node_id):
    return DummyMPModel.objects.get(pk=node_id)


@pytest.mark.django_db
class TestAllowOnlyNodesFromSameTreeForm:
    form_cls = movenodeform_factory(DummyMPModel, form=AllowOnlyNodesFromSameTreeForm)
    tab_str = "&nbsp;&nbsp;&nbsp;&nbsp;"

    def test_choices_include_all_if_instance_empty(self):
        root_node = DummyMPModel.add_root()
        children_node = reload_dummy_node(root_node.pk).add_child()
        leaf_node = reload_dummy_node(children_node.pk).add_child()
        root_node_2 = DummyMPModel.add_root()

        form = self.form_cls()
        assert frozenset(form.declared_fields["_ref_node_id"].choices) == frozenset(
            [
                (None, "-- root --"),
                (root_node.pk, str(root_node)),
                (children_node.pk, 1 * self.tab_str + str(children_node)),
                (leaf_node.pk, 2 * self.tab_str + str(leaf_node)),
                (root_node_2.pk, str(root_node_2)),
            ]
        )

    def test_choices_include_all_rooted_subtree_if_instance_is_root(self):
        root_node = DummyMPModel.add_root()
        children_node = reload_dummy_node(root_node.pk).add_child()
        leaf_node = reload_dummy_node(children_node.pk).add_child()
        root_node_2 = DummyMPModel.add_root()

        form = self.form_cls(instance=root_node)
        assert frozenset(form.declared_fields["_ref_node_id"].choices) == frozenset(
            [
                (None, "-- root --"),
                (root_node.pk, str(root_node)),
                (children_node.pk, 1 * self.tab_str + str(children_node)),
                (leaf_node.pk, 2 * self.tab_str + str(leaf_node)),
                (root_node_2.pk, str(root_node_2)),
            ]
        )

    def test_choices_include_subtree_if_instance_is_children(self):
        root_node = DummyMPModel.add_root()
        children_node = reload_dummy_node(root_node.pk).add_child()
        leaf_node = reload_dummy_node(children_node.pk).add_child()
        DummyMPModel.add_root()

        form = self.form_cls(instance=children_node)
        assert frozenset(form.declared_fields["_ref_node_id"].choices) == frozenset(
            [
                (None, "-- root --"),
                (root_node.pk, str(root_node)),
                (children_node.pk, 1 * self.tab_str + str(children_node)),
                (leaf_node.pk, 2 * self.tab_str + str(leaf_node)),
            ]
        )
