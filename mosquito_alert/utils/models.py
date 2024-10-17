from django.db import models, transaction
from django.db.models.functions import Now
from django.db.models.signals import ModelSignal
from django.utils import timezone
from django.utils.timesince import timesince
from django_lifecycle import LifecycleModelMixin
from treebeard.al_tree import AL_Node
from treebeard.models import Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

parent_has_changed = ModelSignal(use_caching=True)


def update_object_counter(obj, fieldname: str, inc_value: int):
    with transaction.atomic():
        # See: https://docs.djangoproject.com/en/dev/ref/models/expressions/#avoiding-race-conditions-using-f
        setattr(obj, fieldname, models.F(fieldname) + inc_value)
        obj.save(update_fields=[fieldname])
        obj.refresh_from_db(fields=[fieldname])


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

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """An abstract base class model that provides self-updating
    ``created_at`` and ``updated_at`` fields.
    """

    # Relations
    # Attributes - Mandatory

    # Attributes - Optional
    created_at = models.DateTimeField(default=timezone.now, blank=True, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, blank=True, editable=False)

    # Object Manager
    # Custom Properties
    @property
    def created_ago(self) -> str:
        """Humanize date"""
        return timesince(d=self.created_at)

    @property
    def updated_ago(self) -> str:
        """Humanize date"""
        return timesince(d=self.updated_at)

    # Methods
    def __init__(self, *args, **kwargs):
        if not hasattr(self, "pk"):
            # Only on creation
            if not kwargs.get("updated_at", None):
                if created_at := kwargs.get("created_at", None):
                    kwargs["updated_at"] = created_at

        return super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Overriding the save method in order to make sure that
        modified field is updated even if it is not given as
        a parameter to the update field argument.
        """
        update_fields = kwargs.get("update_fields", None)
        if update_fields:
            kwargs["update_fields"] = set(update_fields).union({"updated_at"})

        if not self._state.adding:
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)

    # Meta and String
    class Meta:
        abstract = True

        constraints = [
            models.CheckConstraint(
                check=models.Q(created_at__lte=Now()), name="%(app_label)s_%(class)s_created_at_cannot_be_future_dated"
            ),
            models.CheckConstraint(
                check=models.Q(updated_at__lte=Now()), name="%(app_label)s_%(class)s_updated_at_cannot_be_future_dated"
            ),
            models.CheckConstraint(
                check=models.Q(updated_at__gte=models.F("created_at")),
                name="%(app_label)s_%(class)s_updated_at_must_be_after_created_at",
            ),
        ]


class ObservableMixin(LifecycleModelMixin):
    NOTIFY_ON_FIELD_CHANGE = []

    NOTIFY_ON_CREATE = True
    NOTIFY_ON_DELETE = True

    def _notify_changes(self, fields_changed=[]):
        # The function that is going to be called when changes/create/delete happen
        pass

    def __init__(self, *args, **kwargs):
        # NOTE: __init__ signature can not be changed
        # See: https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model
        self.skip_notify_changes = kwargs.pop("skip_notify_changes", False)
        super().__init__(*args, **kwargs)

    def _get_changed_observable_fields(self):
        return list(filter(lambda x: self.has_changed(field_name=x), self.NOTIFY_ON_FIELD_CHANGE))

    def save(self, *args, **kwargs):
        fields_changed = self._get_changed_observable_fields()
        _is_creating = self._state.adding

        super().save(*args, **kwargs)

        if not self.skip_notify_changes:
            if _is_creating:
                if self.NOTIFY_ON_CREATE:
                    self._notify_changes()
            else:
                if fields_changed:
                    self._notify_changes(fields_changed=fields_changed)

    def delete(self, *args, **kwargs):
        value = super().delete(*args, **kwargs)
        if not self.skip_notify_changes:
            if self.NOTIFY_ON_DELETE:
                self._notify_changes()

        return value
