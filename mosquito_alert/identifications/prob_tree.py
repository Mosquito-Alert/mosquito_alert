from copy import deepcopy
from decimal import ROUND_FLOOR, Decimal, localcontext
from itertools import groupby
from numbers import Number
from typing import Union

from anytree import AnyNode, PreOrderIter, RenderTree, find_by_attr, findall, findall_by_attr
from anytree.exporter import DictExporter

from mosquito_alert.taxa.models import Taxon


def sum_node_probabilities(nodes):
    return sum(x.probability or 0 for x in nodes)


class TaxonProbNode(AnyNode):
    def __init__(self, taxon: Taxon, probability: float = None, is_seed: float = False, **kwargs):
        self.is_seed = is_seed

        self.taxon = taxon
        self.probability = probability

        if self.probability == 0:
            kwargs["parent"] = None

        super().__init__(**kwargs)

    @property
    def is_seed(self) -> bool:
        return self.__dict__.get("is_seed")

    @is_seed.setter
    def is_seed(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("New is_seed value must be boolean")

        self.__dict__.update({"is_seed": value})

    @property
    def taxon(self) -> Taxon:
        return self.__dict__.get("taxon", None)

    @taxon.setter
    def taxon(self, value):
        if value is None:
            raise ValueError("taxon can not be None")

        if not isinstance(value, Taxon):
            raise TypeError("taxon must be an instance of Taxon model.")

        # Avoid taxon update
        if self.taxon:
            raise ValueError("Taxon can not be updated.")

        if parent := self.parent:
            if not value.is_descendant_of(parent.taxon):
                raise ValueError("Taxon must be descedant of its parent taxon.")

        self.__dict__.update({"taxon": value})

    @property
    def probability(self) -> float:
        return self.__dict__.get("probability")

    @probability.setter
    def probability(self, value):
        if self.probability and self.is_seed:
            raise ValueError(f"Tried to modify a probability from a seed node ({self}).")

        if value is None:
            raise ValueError("probabilty can not be None")

        if not isinstance(value, Decimal):
            value = str(value)

        with localcontext() as ctx:
            ctx.prec = 6
            ctx.rounding = ROUND_FLOOR
            value = Decimal(value) * Decimal(1)

        if not 0 <= value <= 1:
            raise ValueError(
                f"Tried to set a probability of {value} for {self} "
                "which is out of the bounds (must be between 0 and 1)."
            )

        old_value = self.probability
        self.__dict__.update({"probability": value})

        if self.probability == 0:
            # Delete from parent
            self.parent = None
        elif old_value != value and self.parent:
            self.parent.update_probability()

    # Custom Properties
    @property
    def to_dict(self) -> dict:
        return DictExporter(
            attriter=lambda attrs: filter(lambda x: not x[0].startswith("_"), attrs),
            childiter=lambda children: sorted(children, key=lambda child: child.taxon.name),
        ).export(self)

    # Methods
    def _apply_func_to_children(self, func, include_self: bool = True, **kwargs) -> None:
        for node in PreOrderIter(self, **kwargs):
            if node is self and not include_self:
                continue
            func(node)

    def _apply_weight(self, weight: float, inplace: bool = False) -> Union["TaxonProbNode", None]:
        tree = self
        if not inplace:
            tree = deepcopy(self)

        seed_nodes = findall_by_attr(node=tree, value=True, name="is_seed")
        # Deactivate seed nodes
        tree._apply_func_to_children(func=lambda x: setattr(x, "is_seed", False), include_self=True)

        weight_decimal = Decimal(str(weight))
        tree._apply_func_to_children(
            func=lambda x: setattr(x, "probability", x.probability * weight_decimal),
            include_self=True,
        )

        # Reactivate nodes that were seeds
        for n in seed_nodes:
            n.is_seed = True

        if not inplace:
            return tree

    def _expand_parent(self) -> "TaxonProbNode":
        if self.taxon.is_root():
            return self

        return TaxonProbNode(taxon=self.taxon.parent, probability=1, children=[self])._expand_parent()

    def _expand_children(self) -> None:
        # Calling all children nodes recursively.
        for c_node in self.children:
            c_node._expand_children()

        if self.taxon.is_leaf():
            return

        missing_probability = max(self.probability - sum_node_probabilities(nodes=self.children), 0)

        if missing_probability == 0:
            return

        # Get descendants that are leafs
        taxon_leafs_qs = self.taxon.get_descendants().filter(numchild=0)

        if self.children:
            represented_leafs = [x.taxon.pk for x in findall(self, filter_=lambda n: n.taxon.is_leaf())]

            taxon_leafs_qs = taxon_leafs_qs.exclude(pk__in=represented_leafs)

        num_missing_taxon_leafs = taxon_leafs_qs.count()

        # No taxons leafs available to share.
        if not num_missing_taxon_leafs:
            return

        # Will share probability equitative for each taxon leaf (specie)
        leaf_prob = missing_probability / num_missing_taxon_leafs
        t_leafs = [TaxonProbNode(taxon=t_leaf, probability=leaf_prob) for t_leaf in taxon_leafs_qs]

        self.link_descendants(nodes=t_leafs)

    def expand_tree(self) -> "TaxonProbNode":
        root_node = self._expand_parent()
        root_node._expand_children()

        return root_node

    def find_by_taxon(self, taxon) -> "TaxonProbNode":
        return find_by_attr(node=self, value=taxon, name="taxon")

    def get_tree_render(self, **kwargs) -> RenderTree:
        return RenderTree(
            node=self, childiter=lambda children: sorted(children, key=lambda child: child.taxon.name), **kwargs
        )

    def link_descendants(self, nodes) -> None:
        # Group nodes by parent:
        #     - key is parent
        #     - value is nodes that has that parent
        g_parent_leaf = groupby(
            sorted(nodes, key=lambda x: x.taxon.parent.pk),
            key=lambda x: x.taxon.parent,
        )

        g_parent_leaf = [(k, list(value)) for k, value in g_parent_leaf]

        if len(g_parent_leaf) == 0:
            return

        deepest_taxon_parent, children = max(g_parent_leaf, key=lambda x: x[0].rank)

        new_nodes = nodes
        # Finding parent in the current tree
        parent = self.find_by_taxon(taxon=deepest_taxon_parent)

        if not parent:
            # Trying to find the parent in the nodes
            parent = list(filter(lambda x: x.taxon == deepest_taxon_parent, nodes))

            if parent:
                parent = parent[0]

        if parent:
            for child in children:
                child.parent = parent
            if parent.taxon.pk == self.taxon.pk:
                return
        else:
            # Create
            parent = TaxonProbNode(
                taxon=deepest_taxon_parent,
                probability=sum_node_probabilities(children),
                children=children,
            )

            new_nodes.append(parent)
        for child in children:
            new_nodes.remove(child)

        if new_nodes:
            self.link_descendants(nodes=nodes)

    def update_probability(self) -> None:
        if not any([self.is_root, self.is_seed]):
            self.probability = sum_node_probabilities(nodes=self.children)

    def _pre_attach(self, parent):
        """Method call before attaching to `parent`."""
        if self.taxon and parent.taxon:
            if not self.taxon.is_descendant_of(parent.taxon):
                raise ValueError("Taxon must be descedant of its parent taxon.")

        if self.taxon in [x.taxon for x in parent.children]:
            raise ValueError(f"Already exist a children with taxon {self.taxon}.")

    def _post_attach(self, parent):
        """Method call after attaching to `parent`."""
        if not self.__dict__.get("__children_update", False):
            parent.update_probability()

    def _post_detach(self, parent):
        """Method call after detaching from `parent`."""
        if not self.__dict__.get("__children_update", False):
            parent.update_probability()

    def _pre_attach_children(self, children):
        """Method call before attaching `children`."""
        self.__dict__.update({"__children_update": True})

    def _post_attach_children(self, children):
        """Method call after attaching `children`."""
        del self.__dict__["__children_update"]
        self.update_probability()

    def _pre_detach_children(self, children):
        """Method call before detaching `children`."""
        self.__dict__.update({"__children_update": True})

    def _post_detach_children(self, children):
        """Method call after detaching `children`."""
        del self.__dict__["__children_update"]
        self.update_probability()

    def __add__(self, other) -> "TaxonProbNode":
        if not other:
            return

        if self.taxon.pk != other.taxon.pk:
            raise ValueError("Can not add probabilities from different taxa nodes.")

        old_children = list(self.children) + list(other.children)
        new_children = []
        for _, children in groupby(sorted(old_children, key=lambda x: x.taxon.pk), key=lambda x: x.taxon.pk):
            children = list(children)
            if len(children) == 1:
                _child = deepcopy(children[0])
                _child.parent = None
                new_children.append(_child)
            elif len(children) > 1:
                new_children.append(sum(children))

        return TaxonProbNode(
            taxon=self.taxon,
            probability=self.probability + other.probability,
            children=new_children,
        )

    def __radd__(self, other) -> "TaxonProbNode":
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other: Number) -> "TaxonProbNode":
        if not isinstance(other, Number):
            raise TypeError("Only numbers are allowed to use when multiplying.")

        return self._apply_weight(weight=other, inplace=False)

    def __repr__(self) -> str:
        s = f"{self.taxon} (p={self.probability})"
        if self.is_seed:
            s += " [seed]"
        return s


def create_tree(nodes: list[TaxonProbNode]) -> TaxonProbNode:
    for n in nodes:
        n.is_seed = True

    # Get the lowest rank shared parent.
    root_taxon = Taxon.get_root()
    root_node_found = list(filter(lambda x: x.taxon.pk == root_taxon.pk, nodes))
    if root_node_found:
        # Root taxon found is one of the identifications.
        parent_node = root_node_found[0]
        nodes.remove(parent_node)
    else:
        if len(nodes) > 1:
            # Intersect all ancestors and get the last() taxon (the deeper)
            common_parent_qs = Taxon.objects.all().intersection(*[x.taxon.get_ancestors() for x in nodes])
            parent_node = TaxonProbNode(taxon=common_parent_qs.last(), probability=1)
        else:
            parent_node = TaxonProbNode(taxon=nodes[0].taxon.parent, probability=1)

    parent_node.link_descendants(nodes=nodes)

    root_node = parent_node.expand_tree()

    if not parent_node.is_seed:
        parent_node.probability = sum_node_probabilities(parent_node.children)

    if root_node.probability != 1:
        raise ValueError("Wrong probability tree.")

    return root_node
