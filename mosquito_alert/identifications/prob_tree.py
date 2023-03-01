import math
from decimal import Decimal
from itertools import groupby

from anytree import AnyNode, PreOrderIter, RenderTree, find_by_attr, findall

from mosquito_alert.taxa.models import Taxon


def get_probabilities_for_nodes(nodes):
    return math.fsum(x.probability or 0 for x in nodes)


def create_tree_from_identifications(identifications):

    # 1. Create all nodes
    nodes = []
    for taxon, probability in identifications:
        nodes.append(TaxonProbNode(taxon=taxon, probability=probability))

    if len(nodes) == 0:
        return None

    # 2. Get the lowest rank shared parent.
    root_taxon = Taxon.get_root_nodes()[0]
    root_node_found = list(filter(lambda x: x.taxon.pk == root_taxon.pk, nodes))
    if root_node_found:
        # Root taxon found is one of the identifications.
        parent_node = root_node_found[0]
        nodes.remove(parent_node)
    else:
        if len(nodes) > 1:
            # Intersect all ancestors and get the last() taxon (the deeper)
            common_parent_qs = Taxon.objects.all().intersection(
                *[x.taxon.get_ancestors() for x in nodes]
            )
            parent_node = TaxonProbNode(taxon=common_parent_qs.last(), probability=1)
        else:
            parent_node = TaxonProbNode(taxon=nodes[0].taxon.parent, probability=1)

    if nodes:
        parent_node.link_descendants(nodes=nodes)

    root_node = parent_node.expand_tree()
    parent_node.probability = get_probabilities_for_nodes(parent_node.children)

    return root_node


class TaxonProbNode(AnyNode):
    def __init__(self, taxon, probability, **kwargs):

        self.taxon = taxon
        self.probability = probability

        super().__init__(**kwargs)

    @property
    def probability(self):
        return self.__dict__.get("probability")

    @probability.setter
    def probability(self, value):
        if not 0 <= value <= 1:
            raise ValueError(
                f"Tried to set a probability of {value} for {self} "
                "which is out of the bounds (must be between 0 and 1)."
            )

        self.__dict__.update({"probability": value})

        if self.probability == 0:
            # Delete in case new probability is 0
            self.parent = None
            del self

    def apply_func_to_children(self, func, include_self=True, **kwargs):
        for node in PreOrderIter(self, **kwargs):
            if not include_self and node is self:
                continue
            func(node)

    def apply_weight(self, weight):
        weight_decimal = Decimal(str(weight))
        self.apply_func_to_children(
            func=lambda x: setattr(
                x, "probability", float(Decimal(str(x.probability)) * weight_decimal)
            ),
            include_self=True,
        )

        return self

    def _expand_parent(self):
        if self.taxon.is_root():
            return self

        return TaxonProbNode(
            taxon=self.taxon.parent, probability=1, children=[self]
        )._expand_parent()

    def _expand_children(self):
        # Calling all children nodes recursively.
        for c_node in self.children:
            c_node._expand_children()

        if self.taxon.is_leaf():
            return

        missing_probability = max(
            self.probability - get_probabilities_for_nodes(nodes=self.children), 0
        )

        if missing_probability == 0:
            return

        # Get descendants that are leafs
        taxon_leafs_qs = self.taxon.get_descendants().filter(numchild=0)

        if self.children:
            represented_leafs = [
                x.taxon.pk for x in findall(self, filter_=lambda n: n.taxon.is_leaf())
            ]

            taxon_leafs_qs = taxon_leafs_qs.exclude(pk__in=represented_leafs)

        num_missing_taxon_leafs = taxon_leafs_qs.count()

        # No taxons leafs available to share.
        if not num_missing_taxon_leafs:
            return

        # Will share probability equitative for each taxon leaf (specie)
        leaf_prob = missing_probability / num_missing_taxon_leafs
        t_leafs = [
            TaxonProbNode(taxon=t_leaf, probability=leaf_prob)
            for t_leaf in taxon_leafs_qs
        ]

        self.link_descendants(nodes=t_leafs)

    def expand_tree(self):

        root_node = self._expand_parent()
        root_node._expand_children()

        return root_node

    def find_by_taxon(self, taxon):
        return find_by_attr(node=self, value=taxon, name="taxon")

    def get_tree_render(self, **kwargs):
        return RenderTree(node=self, **kwargs)

    def link_descendants(self, nodes):
        # Group nodes by parent
        g_parent_leaf = groupby(
            sorted(nodes, key=lambda x: x.taxon.parent.pk),
            key=lambda x: x.taxon.parent,
        )

        g_parent_leaf = [(k, list(value)) for k, value in g_parent_leaf]

        deepest_taxon_parent, children = max(g_parent_leaf, key=lambda x: x[0].rank)

        new_nodes = nodes
        parent = list(filter(lambda x: x.taxon == deepest_taxon_parent, nodes + [self]))
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
                probability=get_probabilities_for_nodes(children),
                children=children,
            )

            new_nodes.append(parent)
        for child in children:
            new_nodes.remove(child)

        if new_nodes:
            self.link_descendants(nodes=nodes)

    def __add__(self, other):

        if not other:
            return

        if self.taxon.pk != other.taxon.pk:
            raise ValueError("Can not add probabilities from different taxa nodes.")

        old_children = list(self.children) + list(other.children)
        new_children = []
        for _, children in groupby(
            sorted(old_children, key=lambda x: x.taxon.pk), key=lambda x: x.taxon.pk
        ):
            children = list(children)
            if len(children) == 1:
                new_children += children
            elif len(children) > 1:
                value = sum(children)
                if value:
                    new_children.append(value)

        return TaxonProbNode(
            taxon=self.taxon,
            probability=self.probability + other.probability,
            children=new_children,
        )

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __repr__(self):
        return f"{self.taxon} (p={self.probability})"
