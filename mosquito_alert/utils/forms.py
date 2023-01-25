from django import forms
from django.utils.translation import gettext_lazy as _
from treebeard.forms import MoveNodeForm as OriginalMoveNodeForm

from .models import ParentManageableNodeMixin


class AllowOnlyNodesFromSameTreeFormMixin:
    @classmethod
    def mk_dropdown_tree(cls, model, for_node=None):
        """Creates a tree-like list of choices"""
        options = [(None, _("-- root --"))]

        if for_node:
            if for_node.is_root():
                for node in model.get_root_nodes():
                    cls.add_subtree(for_node, node, options)
            else:
                # Only select its tree.
                cls.add_subtree(for_node, for_node.get_root(), options)
        else:
            # Select all
            for node in model.get_root_nodes():
                cls.add_subtree(for_node, node, options)
        return options


class AllowOnlyNodesFromSameTreeForm(
    OriginalMoveNodeForm, AllowOnlyNodesFromSameTreeFormMixin
):
    pass


class ParentManageableNodeFormMixin:
    def save(self, commit=True):
        position_type, reference_node_id = self._clean_cleaned_data()

        ref_is_parent = position_type.endswith("child")
        parent_node = None
        if reference_node_id:
            parent_node = self._meta.model.objects.get(pk=reference_node_id)
            if not ref_is_parent:
                parent_node = parent_node.get_parent()

        self.instance.parent = parent_node

        forms.ModelForm.save(self, commit=commit)
        return self.instance


class ParentManageableMoveNodeForm(ParentManageableNodeFormMixin, OriginalMoveNodeForm):
    @classmethod
    def _check_instance_class(cls, instance):
        if not instance or not issubclass(
            instance.__class__, ParentManageableNodeMixin
        ):
            raise ValueError(
                "{} only can be used with instances that subclass {}".format(
                    cls.__name__, ParentManageableNodeMixin.__name__
                )
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._check_instance_class(instance=self.instance)


class MoveNodeForm(OriginalMoveNodeForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get("intance", None)

        try:
            ParentManageableMoveNodeForm._check_instance_class(instance=instance)
        except ValueError:
            pass
        else:
            self.__class__ = ParentManageableMoveNodeForm

        super().__init__(*args, **kwargs)
