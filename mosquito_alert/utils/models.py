from django.db.models.signals import ModelSignal, post_save
from django.utils.functional import cached_property
from treebeard.al_tree import AL_Node
from treebeard.models import Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

parent_has_changed = ModelSignal(use_caching=True)


def move_node(sender, instance, *args, **kwargs):

    if "parent" in instance.__dict__.keys():
        # If parent has changed or been called
        if instance.get_parent() != instance.parent:
            parent_has_changed.send(sender=instance.__class__, instance=instance)
            # If parent property has changed
            is_sorted = getattr(instance, "node_order_by", False)
            pos_preffix = "sorted" if is_sorted else "first"
            if instance.parent:
                assert isinstance(instance.parent, instance._meta.model)
                instance.move(target=instance.parent, pos=f"{pos_preffix}-child")
            else:
                instance.move(
                    target=instance._meta.model.get_first_root_node(),
                    pos=f"{pos_preffix}-sibling",
                )
            # TODO: not sure if it is needed
            # Need to reload to not override them
            # when super().save is called.
            instance.refresh_from_db()


class ParentManageableNodeMixin(Node):
    @classmethod
    def __init_subclass__(cls, **kwargs):
        # Make subclasses connect to the signals.
        super().__init_subclass__(**kwargs)
        post_save.connect(move_node, sender=cls)

    @cached_property
    def parent(self):
        return self.get_parent()

    @classmethod
    def _get_mandatory_field(cls):
        if issubclass(cls, MP_Node):
            return "path"
        elif issubclass(cls, AL_Node):
            # TODO: raise because it will cause problems with the 'parent' cached_property
            raise NotImplementedError(f"{cls} has not been impleted to use this mixin.")
        elif issubclass(cls, NS_Node):
            return "lft"
        else:
            raise NotImplementedError(f"{cls} has not been impleted to use this mixin.")

    def save(self, *args, **kwargs):

        if self._state.adding and not getattr(self, self._get_mandatory_field(), None):
            # If first time adding into DB and mandatory_fields still not set.
            # mandatory_fields are set inside add_root/add_child methods
            if "parent" in self.__dict__:
                if self.parent:
                    # If parent is not None
                    assert isinstance(self.parent, self._meta.model)
                    self = self.parent.add_child(instance=self)
                else:
                    self = self._meta.model.add_root(instance=self)
                # Return since save() is already called inside add_child/add_root
                return

        # This method will be called when:
        #     - creating new object and mandatory fields already set (add_child/add_root set them)
        #     - all other scenarios
        super().save(*args, **kwargs)

    class Meta:
        """Abstract model."""

        abstract = True
