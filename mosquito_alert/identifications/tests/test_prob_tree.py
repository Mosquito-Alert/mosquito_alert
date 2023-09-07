from contextlib import nullcontext as does_not_raise
from decimal import Decimal
from unittest.mock import patch

import pytest
from anytree import RenderTree

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory

from ..prob_tree import create_tree, sum_node_probabilities
from .factories import TaxonProbNodeFactory


@pytest.mark.django_db
def test_sum_node_probabilities(taxon_specie):
    nodes = [
        TaxonProbNodeFactory(probability=1, taxon=taxon_specie),
        TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie),
    ]

    sum_probabilities = 1 + 0.1
    assert sum_node_probabilities(nodes=nodes) == Decimal(str(sum_probabilities))


def test_create_tree_does_keep_seed_enabled(taxon_root):
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

    node_class1 = TaxonProbNodeFactory(probability=0.8, taxon=taxon_class1)
    node_class2 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_class2)

    create_tree(nodes=[node_class1, node_class2])

    assert node_class1.is_seed
    assert node_class2.is_seed
    assert not node_class1.root.is_seed


@pytest.mark.django_db
def test_create_tree_with_only_species(taxon_root):
    # Creating a simple taxonomy tree
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

    node_specie1_1 = TaxonProbNodeFactory(probability=0.7, taxon=taxon_specie1_1)
    node_specie2_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1)

    tree = create_tree(nodes=[node_specie1_1, node_specie2_1])

    expected_tree_root = TaxonProbNodeFactory(
        probability=1,
        taxon=taxon_root,
        children=[
            TaxonProbNodeFactory(
                probability=0.8,
                taxon=taxon_class1,
                children=[
                    TaxonProbNodeFactory(probability=0.7, taxon=taxon_specie1_1, is_seed=True),
                    TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie1_2),
                ],
            ),
            TaxonProbNodeFactory(
                probability=0.2,
                taxon=taxon_class2,
                children=[TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1, is_seed=True)],
            ),
        ],
    )

    assert tree.to_dict == expected_tree_root.to_dict


@pytest.mark.django_db
def test_create_tree_with_mixed_ranks(taxon_root):
    # Creating a simple taxonomy tree
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

    node_class1 = TaxonProbNodeFactory(probability=0.8, taxon=taxon_class1)
    node_specie2_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1)

    tree = create_tree(nodes=[node_class1, node_specie2_1])

    expected_tree_root = TaxonProbNodeFactory(
        probability=1,
        taxon=taxon_root,
        children=[
            TaxonProbNodeFactory(
                probability=0.8,
                taxon=taxon_class1,
                is_seed=True,
                children=[
                    TaxonProbNodeFactory(probability=0.4, taxon=taxon_specie1_1),
                    TaxonProbNodeFactory(probability=0.4, taxon=taxon_specie1_2),
                ],
            ),
            TaxonProbNodeFactory(
                probability=0.2,
                taxon=taxon_class2,
                children=[TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1, is_seed=True)],
            ),
        ],
    )

    assert tree.to_dict == expected_tree_root.to_dict


@pytest.mark.django_db
def test_create_tree_with_invalid_combination_exceed_probability(taxon_root):
    # Creating a simple taxonomy tree
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    _ = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

    node_specie1_1 = TaxonProbNodeFactory(probability=0.7, taxon=taxon_specie1_1)
    node_specie2_1 = TaxonProbNodeFactory(probability=0.7, taxon=taxon_specie2_1)

    with pytest.raises(ValueError):
        _ = create_tree(nodes=[node_specie1_1, node_specie2_1])


@pytest.mark.django_db
def test_create_tree_lose_probability(taxon_root):
    # Creating a simple taxonomy tree
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

    node_specie1_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_1)
    node_specie1_2 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_2)
    node_specie2_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1)

    with pytest.raises(ValueError):
        _ = create_tree(nodes=[node_specie1_1, node_specie1_2, node_specie2_1])


@pytest.mark.django_db
def test_create_tree_wrong_probability_with_seeds(taxon_root):
    # Creating a simple taxonomy tree
    taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
    taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
    taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

    node_class1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_1)
    node_specie1_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_1)
    node_specie1_2 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_2)
    node_specie2_1 = TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie2_1)

    with pytest.raises(ValueError):
        _ = create_tree(nodes=[node_class1, node_specie1_1, node_specie1_2, node_specie2_1])


@pytest.mark.django_db
class TestTaxonProbNode:
    # fields
    def test_is_seed_is_default_False(self, taxon_root):
        assert TaxonProbNodeFactory(taxon=taxon_root).is_seed is False

    def test_is_seed_can_be_set_on_create(self, taxon_root):
        assert TaxonProbNodeFactory(taxon=taxon_root, is_seed=True).is_seed

    def test_is_seed_can_be_set_after_create(self, taxon_root):
        obj = TaxonProbNodeFactory(taxon=taxon_root)

        obj.is_seed = False
        assert obj.is_seed is False

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            ("False", pytest.raises(ValueError)),
            (1, pytest.raises(ValueError)),
            ([], pytest.raises(ValueError)),
            (True, does_not_raise()),
        ],
    )
    def test_is_seed_setter_raise_if_new_value_is_not_bool(self, taxon_root, value, expected_raise):
        obj = TaxonProbNodeFactory(taxon=taxon_root)

        with expected_raise:
            obj.is_seed = value

    def test_taxon_can_not_be_None(self):
        with pytest.raises(ValueError):
            TaxonProbNodeFactory(taxon=None)

    def test_taxon_must_be_Taxon_instance(self):
        with pytest.raises(TypeError):
            TaxonProbNodeFactory(taxon=object())

    def test_taxon_can_not_be_updated_once_set(self, taxon_root, taxon_specie):
        obj = TaxonProbNodeFactory(taxon=taxon_root)

        with pytest.raises(ValueError):
            obj.taxon = taxon_specie

    def test_taxon_must_be_descendant_of_its_parent_taxon(self, taxon_root, taxon_specie):
        parent = TaxonProbNodeFactory(taxon=taxon_specie)

        with pytest.raises(ValueError):
            TaxonProbNodeFactory(parent=parent, taxon=taxon_root)

    def test_on_create_taxon_must_be_descendant_of_parent(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        node_class2 = TaxonProbNodeFactory(taxon=taxon_class2)

        with pytest.raises(ValueError):
            TaxonProbNodeFactory(taxon=taxon_specie1_2, parent=node_class2)

    def test_probability_can_not_edit_ifis_seed(self, taxon_root):
        node_root = TaxonProbNodeFactory(taxon=taxon_root)
        node_root.is_seed = True

        with pytest.raises(ValueError):
            node_root.probability = 1

    def test_probability_can_not_be_None(self, taxon_root):
        with pytest.raises(ValueError):
            TaxonProbNodeFactory(probability=None, taxon=taxon_root)

    @pytest.mark.parametrize(
        "value, expected_result",
        [
            (0.5, Decimal("0.5")),
            ("0.5", Decimal("0.5")),
            (1, Decimal("1")),
            (Decimal(0.5), Decimal("0.5")),
            (0.123456789, Decimal("0.123456")),
            ("0.5000", Decimal("0.5")),
            (1.0000000001, Decimal("1")),
            (0.6666666666666, Decimal("0.666666")),
            (Decimal(0.52134598234563), Decimal("0.521345")),
        ],
    )
    def test_probability_is_cast_to_Decimal_precicion_6(self, taxon_root, value, expected_result):
        node = TaxonProbNodeFactory(probability=value, taxon=taxon_root)
        assert node.probability == expected_result

    @pytest.mark.parametrize(
        "value, expected_raise",
        [
            (0, does_not_raise()),
            (1, does_not_raise()),
            (-0.1, pytest.raises(ValueError)),
            (1.1, pytest.raises(ValueError)),
        ],
    )
    def test_probability_valid_range_from_0_to_1(self, value, expected_raise, taxon_specie):
        with expected_raise:
            TaxonProbNodeFactory(probability=value, taxon=taxon_specie)

    def test_probability_0_disconnects_from_parent_on_create(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        root = TaxonProbNodeFactory(taxon=taxon_root, probability=1)
        children1 = TaxonProbNodeFactory(probability=0, taxon=taxon_class1, parent=root)
        _ = TaxonProbNodeFactory(taxon=taxon_specie1_1, parent=children1)
        children2 = TaxonProbNodeFactory(taxon=taxon_class2, parent=root)
        children2_1 = TaxonProbNodeFactory(taxon=taxon_specie2_1, parent=children2)

        assert children1.probability == 0
        assert children1.parent is None
        assert root.children == (children2,)
        assert root.descendants == (children2, children2_1)
        assert root.leaves == (children2_1,)

    def test_probability_0_disconnects_from_parent_after_create(self, taxon_root, taxon_specie):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        root = TaxonProbNodeFactory(taxon=taxon_root, probability=1)
        children1 = TaxonProbNodeFactory(taxon=taxon_class1, parent=root)
        children2 = TaxonProbNodeFactory(taxon=taxon_class2, parent=root)

        assert root.children == (children1, children2)

        children1.probability = 0

        assert root.children == (children2,)

    def test_probability_only_update_calls_parent_udpate_probability(self, taxon_root, taxon_specie):
        root_node = TaxonProbNodeFactory(taxon=taxon_root, probability=1)
        children = TaxonProbNodeFactory(taxon=taxon_specie, probability=1, parent=root_node)

        with patch.object(root_node, "update_probability", return_value=None) as mock_method:
            children.probability = 1
            mock_method.assert_not_called()

            children.probability = 0.5
            mock_method.assert_called_once()

    # properties
    def test_to_dict(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Check: children are sorted by namme and is_seed is not shown.
        root_node = TaxonProbNodeFactory(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNodeFactory(
                    taxon=taxon_class2,
                    probability=0.2,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie2_1, probability=0.2),
                    ],
                ),
                TaxonProbNodeFactory(
                    taxon=taxon_class1,
                    probability=0.8,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=0.4),
                        TaxonProbNodeFactory(taxon=taxon_specie1_1, probability=0.4),
                    ],
                ),
            ],
        )

        assert root_node.to_dict == {
            "taxon": taxon_root,
            "probability": 1,
            "is_seed": False,
            "children": [
                {
                    "taxon": taxon_class1,
                    "probability": Decimal("0.8"),
                    "is_seed": False,
                    "children": [
                        {"taxon": taxon_specie1_1, "probability": Decimal("0.4"), "is_seed": False},
                        {"taxon": taxon_specie1_2, "probability": Decimal("0.4"), "is_seed": False},
                    ],
                },
                {
                    "taxon": taxon_class2,
                    "probability": Decimal("0.2"),
                    "is_seed": False,
                    "children": [{"taxon": taxon_specie2_1, "probability": Decimal("0.2"), "is_seed": False}],
                },
            ],
        }

    # methods
    @pytest.mark.parametrize("include_self", [True, False])
    def test_apply_func_to_children_calls_func_in_all_nodes(self, taxon_root, include_self):
        func_calls = []

        def func(x):
            return func_calls.append(x)

        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        root = TaxonProbNodeFactory(taxon=taxon_root)
        children1 = TaxonProbNodeFactory(taxon=taxon_class1, parent=root)
        children1_1 = TaxonProbNodeFactory(taxon=taxon_specie1_1, parent=children1)
        children2 = TaxonProbNodeFactory(taxon=taxon_class2, parent=root)
        children2_1 = TaxonProbNodeFactory(taxon=taxon_specie2_1, parent=children2)

        root._apply_func_to_children(func=func, include_self=include_self)

        expected_result = [children1, children1_1, children2, children2_1]
        if include_self:
            expected_result = [root] + expected_result
        assert func_calls == expected_result

    @pytest.mark.parametrize("inplace", [True, False])
    def test_apply_weight(self, taxon_root, inplace):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Create nodes
        root = TaxonProbNodeFactory(probability=1, taxon=taxon_root)
        children1 = TaxonProbNodeFactory(probability=0.75, taxon=taxon_class1, parent=root)
        children1_1 = TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie1_1, parent=children1, is_seed=True)
        children2 = TaxonProbNodeFactory(probability=0.25, taxon=taxon_class2, parent=root)
        children2_1 = TaxonProbNodeFactory(probability=0.25, taxon=taxon_specie2_1, parent=children2)

        result_tree = root._apply_weight(weight=0.5, inplace=inplace)
        if inplace:
            assert result_tree is None
            result_tree = root

        expected_tree = TaxonProbNodeFactory(
            taxon=root.taxon,
            probability=0.5,
            children=[
                TaxonProbNodeFactory(
                    taxon=children1.taxon,
                    probability=0.375,
                    children=[TaxonProbNodeFactory(taxon=children1_1.taxon, probability=0.375, is_seed=True)],
                ),
                TaxonProbNodeFactory(
                    taxon=children2.taxon,
                    probability=0.125,
                    children=[
                        TaxonProbNodeFactory(
                            taxon=children2_1.taxon,
                            probability=0.125,
                        )
                    ],
                ),
            ],
        )

        assert result_tree.to_dict == expected_tree.to_dict

    def test_expand_parent_with_root_taxon(self, taxon_root):
        node = TaxonProbNodeFactory(taxon=taxon_root)
        assert node.ancestors == ()

        assert node._expand_parent() == node

    def test_expand_parent_with_non_root_taxon(self, taxon_root):
        taxon_class = TaxonFactory(rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie = TaxonFactory(rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class)

        species_node = TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie)
        assert species_node.ancestors == ()

        result = species_node._expand_parent()

        expected_result_tree = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=1,
                    taxon=taxon_class,
                    children=[TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie)],
                )
            ],
        )

        assert result.to_dict == expected_result_tree.to_dict

    def test_expand_children(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        node = TaxonProbNodeFactory(probability=1, taxon=taxon_root)
        assert node.descendants == ()

        node._expand_children()

        expected_tree_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=2 / 3,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=1 / 3, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=1 / 3, taxon=taxon_specie1_2),
                    ],
                ),
                TaxonProbNodeFactory(
                    probability=1 / 3,
                    taxon=taxon_class2,
                    children=[TaxonProbNodeFactory(probability=1 / 3, taxon=taxon_specie2_1)],
                ),
            ],
        )

        assert node.to_dict == expected_tree_root.to_dict

    def test_expand_tree(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        species_node = TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie1_1)
        assert species_node.descendants == ()

        root_node = species_node.expand_tree()

        expected_tree_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=1,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.25, taxon=taxon_specie1_2),
                    ],
                )
            ],
        )

        assert root_node.to_dict == expected_tree_root.to_dict

        class_node = TaxonProbNodeFactory(probability=0.75, taxon=taxon_class1)
        root_node = class_node.expand_tree()

        expected_tree_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=0.75,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.375, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.375, taxon=taxon_specie1_2),
                    ],
                ),
                TaxonProbNodeFactory(
                    probability=0.25,
                    taxon=taxon_class2,
                    children=[
                        TaxonProbNodeFactory(probability=0.25, taxon=taxon_specie2_1),
                    ],
                ),
            ],
        )

        assert root_node.to_dict == expected_tree_root.to_dict

    def test_find_by_taxon(self, taxon_root, taxon_specie):
        root = TaxonProbNodeFactory(taxon=taxon_root)
        children = TaxonProbNodeFactory(taxon=taxon_specie, parent=root)

        assert root.find_by_taxon(taxon=taxon_specie) == children

    def test_find_by_taxon_only_looks_at_descendants(self, taxon_root, taxon_specie):
        root = TaxonProbNodeFactory(taxon=taxon_root)
        children = TaxonProbNodeFactory(taxon=taxon_specie, parent=root)

        assert children.find_by_taxon(taxon=taxon_root) is None

    def test_find_by_taxon_non_exist_return_None(self, taxon_root, taxon_specie):
        node = TaxonProbNodeFactory(taxon=taxon_root)
        assert node.find_by_taxon(taxon=taxon_specie) is None

    def test_get_tree_render(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Check: children are sorted by namme and is_seed is not shown.
        root_node = TaxonProbNodeFactory(
            taxon=taxon_root,
            probability=1,
            children=[
                TaxonProbNodeFactory(
                    taxon=taxon_class2,
                    probability=0.2,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie2_1, probability=0.2),
                    ],
                ),
                TaxonProbNodeFactory(
                    taxon=taxon_class1,
                    probability=0.8,
                    children=[
                        TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=0.4),
                        TaxonProbNodeFactory(taxon=taxon_specie1_1, probability=0.4),
                    ],
                ),
            ],
        )

        tree_render = root_node.get_tree_render()

        assert isinstance(tree_render, RenderTree)
        assert tree_render.node == root_node

        # Check children order is by name
        expected_str = "\n".join(
            [
                f"{taxon_root} (p=1)",
                f"├── {taxon_class1} (p=0.8)",
                f"│   ├── {taxon_specie1_1} (p=0.4)",
                f"│   └── {taxon_specie1_2} (p=0.4)",
                f"└── {taxon_class2} (p=0.2)",
                f"    └── {taxon_specie2_1} (p=0.2)",
            ]
        )

        assert str(tree_render) == expected_str

    def test_link_descendants(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        node_root = TaxonProbNodeFactory(probability=1, taxon=taxon_root)
        node_specie1_1 = TaxonProbNodeFactory(probability=0.8, taxon=taxon_specie1_1)
        node_specie1_2 = TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie1_2)
        node_specie2_1 = TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie2_1)

        node_root.link_descendants(nodes=[node_specie1_1, node_specie1_2, node_specie2_1])

        expected_tree_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=0.9,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.8, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie1_2),
                    ],
                ),
                TaxonProbNodeFactory(
                    probability=0.1,
                    taxon=taxon_class2,
                    children=[TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie2_1)],
                ),
            ],
        )

        assert node_root.to_dict == expected_tree_root.to_dict

    def test_update_probability_runs_only_if_not_root_and_not_seed(self, taxon_root, monkeypatch):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)

        node_root = TaxonProbNodeFactory(probability=0.5, taxon=taxon_root)
        node_class1 = TaxonProbNodeFactory(probability=0.5, taxon=taxon_class1, parent=node_root)
        node_specie1_1 = TaxonProbNodeFactory(probability=1, taxon=taxon_specie1_1)
        # Let's say the specie was the seed annotation
        node_specie1_1.is_seed = True
        node_specie1_1.parent = node_class1

        node_specie1_1.update_probability()
        assert node_specie1_1.probability == 1  # is seed

        node_class1.update_probability()
        assert node_class1.probability == 1  # is not root neither seed
        assert node_root.probability == 0.5  # is root

    def test_taxon_is_checked_before_parent_attach(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        node_class2 = TaxonProbNodeFactory(taxon=taxon_class2)
        node_specie1_2 = TaxonProbNodeFactory(taxon=taxon_specie1_2)

        with pytest.raises(ValueError):
            node_specie1_2.parent = node_class2

    def test_taxon_is_checked_among_children_before_parent_attach(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)

        node_root = TaxonProbNodeFactory(taxon=taxon_root)
        _ = TaxonProbNodeFactory(taxon=taxon_class1, parent=node_root)
        node_class1_other = TaxonProbNodeFactory(taxon=taxon_class1)

        with pytest.raises(ValueError):
            node_class1_other.parent = node_root

    def test_probability_is_updated_after_new_parent_attach(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)

        node_root = TaxonProbNodeFactory(taxon=taxon_root, probability=1)
        node_class1 = TaxonProbNodeFactory(taxon=taxon_class1, probability=0.1, parent=node_root)
        node_specie1_2 = TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=1)

        assert node_root.probability == 1
        assert node_class1.probability == Decimal("0.1")
        assert node_specie1_2.probability == 1

        node_specie1_2.parent = node_class1

        assert node_class1.probability == 1
        assert node_root.probability == 1

    def test_probability_is_updated_after_parent_dettach(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)

        node_root = TaxonProbNodeFactory(taxon=taxon_root, probability=1)
        node_class1 = TaxonProbNodeFactory(taxon=taxon_class1, probability=1, parent=node_root)
        node_specie1_2 = TaxonProbNodeFactory(taxon=taxon_specie1_2, probability=1, parent=node_class1)

        assert node_root.probability == 1
        assert node_class1.probability == 1
        assert node_specie1_2.probability == 1

        node_specie1_2.parent = None

        assert node_class1.probability == 0
        assert node_root.probability == 1

    def test__add__fail_if_different_taxon(self, taxon_root, taxon_specie):
        node_root = TaxonProbNodeFactory(taxon=taxon_root)
        node_specie = TaxonProbNodeFactory(taxon=taxon_specie)

        with pytest.raises(ValueError):
            node_root + node_specie

    def test__add__and__radd__(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_specie1_2 = TaxonFactory(name="specie1_2", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Tree 1
        t1_node_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=1,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.8, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.2, taxon=taxon_specie1_2),
                    ],
                )
            ],
        )

        # Tree 2
        t2_node_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=0.7,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.6, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.1, taxon=taxon_specie1_2),
                    ],
                ),
                TaxonProbNodeFactory(
                    probability=0.3,
                    taxon=taxon_class2,
                    children=[TaxonProbNodeFactory(probability=0.3, taxon=taxon_specie2_1)],
                ),
            ],
        )

        t1_node_root = t1_node_root * 0.5
        t2_node_root = t2_node_root * 0.5

        expected_tree_root = TaxonProbNodeFactory(
            probability=1,
            taxon=taxon_root,
            children=[
                TaxonProbNodeFactory(
                    probability=0.85,
                    taxon=taxon_class1,
                    children=[
                        TaxonProbNodeFactory(probability=0.7, taxon=taxon_specie1_1),
                        TaxonProbNodeFactory(probability=0.15, taxon=taxon_specie1_2),
                    ],
                ),
                TaxonProbNodeFactory(
                    probability=0.15,
                    taxon=taxon_class2,
                    children=[TaxonProbNodeFactory(probability=0.15, taxon=taxon_specie2_1)],
                ),
            ],
        )

        # __add__
        result = t1_node_root + t2_node_root

        assert result.to_dict == expected_tree_root.to_dict

        # __radd__
        result = sum([t1_node_root])
        assert result == t1_node_root
        result = sum([t1_node_root, t2_node_root])

        assert result.to_dict == expected_tree_root.to_dict

    def test__mul__raise_if_input_not_a_Number(self, taxon_root):
        node_root = TaxonProbNodeFactory(taxon=taxon_root)

        with pytest.raises(TypeError):
            node_root * "str"

    def test__mul__(self, taxon_root):
        # Creating a simple taxonomy tree
        taxon_class1 = TaxonFactory(name="class1", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie1_1 = TaxonFactory(name="specie1_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class1)
        taxon_class2 = TaxonFactory(name="class2", rank=Taxon.TaxonomicRank.CLASS, parent=taxon_root)
        taxon_specie2_1 = TaxonFactory(name="specie2_1", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_class2)

        # Create nodes
        root = TaxonProbNodeFactory(probability=1, taxon=taxon_root)
        children1 = TaxonProbNodeFactory(probability=0.75, taxon=taxon_class1, parent=root)
        children1_1 = TaxonProbNodeFactory(probability=0.75, taxon=taxon_specie1_1, parent=children1, is_seed=True)
        children2 = TaxonProbNodeFactory(probability=0.25, taxon=taxon_class2, parent=root)
        children2_1 = TaxonProbNodeFactory(probability=0.25, taxon=taxon_specie2_1, parent=children2)

        result_tree = root * 0.5

        expected_tree = TaxonProbNodeFactory(
            taxon=root.taxon,
            probability=0.5,
            children=[
                TaxonProbNodeFactory(
                    taxon=children1.taxon,
                    probability=0.375,
                    children=[TaxonProbNodeFactory(taxon=children1_1.taxon, probability=0.375, is_seed=True)],
                ),
                TaxonProbNodeFactory(
                    taxon=children2.taxon,
                    probability=0.125,
                    children=[
                        TaxonProbNodeFactory(
                            taxon=children2_1.taxon,
                            probability=0.125,
                        )
                    ],
                ),
            ],
        )

        assert result_tree.to_dict == expected_tree.to_dict

    @pytest.mark.parametrize("is_seed", [True, False])
    def test__repr__(self, taxon_root, is_seed):
        node = TaxonProbNodeFactory(probability=0.666, taxon=taxon_root, is_seed=is_seed)

        s = f"{taxon_root} (p=0.666)"
        if is_seed:
            s += " [seed]"

        assert str(node) == s
