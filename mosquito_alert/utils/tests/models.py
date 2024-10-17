from django.db import models
from treebeard.al_tree import AL_Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

from ..models import NodeExpandedQueriesMixin, ObservableMixin, ParentManageableNodeMixin, TimeStampedModel


class DummyMPModel(MP_Node):
    pass


class DummyMP_NodeParentManageableModel(ParentManageableNodeMixin, MP_Node):
    pass


class DummyAL_NodeParentManageableModel(ParentManageableNodeMixin, AL_Node):
    pass


class DummyNS_NodeParentManageableModel(ParentManageableNodeMixin, NS_Node):
    pass


class DummyNonNodeParentManageableModel(ParentManageableNodeMixin):
    pass


class DummyMP_NodeExpandedQueriesModel(NodeExpandedQueriesMixin, MP_Node):
    pass


class DummyTimeStampedModel(TimeStampedModel):
    class Meta(TimeStampedModel.Meta):
        pass


class DummyObservableModel(ObservableMixin, models.Model):
    NOTIFY_ON_FIELD_CHANGE = ["name"]

    name = models.CharField(max_length=20)
    hidden_name = models.CharField(max_length=20)


class DummyCounterModel(models.Model):
    counter = models.IntegerField(default=0)
