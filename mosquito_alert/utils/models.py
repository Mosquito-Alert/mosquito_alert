from django.db.models.signals import ModelSignal
from treebeard.al_tree import AL_Node
from treebeard.models import Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

parent_has_changed = ModelSignal(use_caching=True)


class ParentManageableNodeMixin(Node):
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # if parent := kwargs.pop("parent", None):
        #    self.parent = parent

    @property
    def parent(self):
        if "parent" not in self.__dict__.keys():
            try:
                self.parent = self.get_parent()
            except Exception:
                return None

        return self.__dict__["parent"]

    @parent.setter
    def parent(self, value):
        res = self.__dict__["parent"] = value
        return res

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new:
            if not getattr(self, self._get_mandatory_field(), None):
                # If first time adding into DB and mandatory_fields still not set.
                # mandatory_fields are set inside add_root/add_child methods
                if self.parent:
                    assert isinstance(self.parent, self._meta.model)
                    self = self.parent.add_child(instance=self)
                else:
                    # Add as root
                    self = self._meta.model.add_root(instance=self)
                # Return since save() is already called inside add_child/add_root
                return

        # This method will be called when:
        #     - creating new object and mandatory fields already set (add_child/add_root set them)
        #     - all other scenarios
        super().save(*args, **kwargs)

        if not is_new:
            if "parent" in self.__dict__.keys():
                # If parent has changed or been called
                if self.get_parent() != self.parent:
                    parent_has_changed.send(sender=self.__class__, instance=self)
                    # If parent property has changed
                    is_sorted = getattr(self, "node_order_by", False)
                    pos_preffix = "sorted" if is_sorted else "first"
                    if self.parent:
                        assert isinstance(self.parent, self._meta.model)
                        self.move(target=self.parent, pos=f"{pos_preffix}-child")
                    else:
                        self.move(
                            target=self._meta.model.get_first_root_node(),
                            pos=f"{pos_preffix}-sibling",
                        )
                    # Need to reload to not override them
                    # when super().save is called.
                    self.refresh_from_db()

    class Meta:
        abstract = True


class NodeExpandedQueriesMixin(Node):
    def get_ancestors_and_self(self):
        """
        Gets ancestors and includes itself. Use treebeard's get_ancestors
        if you don't want to include the category itself.
        """
        if self.is_root():
            return [self]

        return list(self.get_ancestors()) + [self]

    def get_descendants_and_self(self):
        """
        Gets descendants and includes itself. Use treebeard's get_descendants
        if you don't want to include the category itself.
        """
        return self.get_tree(self)

    def get_num_children(self):
        return self.get_children().count()

    def has_children(self):
        return self.get_num_children() > 0

    class Meta:
        abstract = True
