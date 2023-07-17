from treebeard.al_tree import AL_Node
from treebeard.mp_tree import MP_Node
from treebeard.ns_tree import NS_Node

from ..models import NodeExpandedQueriesMixin, ParentManageableNodeMixin


class DummyMPModel(MP_Node):
    class Meta:
        app_label = "utils_test"


class DummyMP_NodeParentManageableModel(ParentManageableNodeMixin, MP_Node):
    class Meta:
        app_label = "utils_test"


class DummyAL_NodeParentManageableModel(ParentManageableNodeMixin, AL_Node):
    class Meta:
        app_label = "utils_test"


class DummyNS_NodeParentManageableModel(ParentManageableNodeMixin, NS_Node):
    class Meta:
        app_label = "utils_test"


class DummyNonNodeParentManageableModel(ParentManageableNodeMixin):
    class Meta:
        app_label = "utils_test"


class DummyMP_NodeExpandedQueriesModel(NodeExpandedQueriesMixin, MP_Node):
    class Meta:
        app_label = "utils_test"
