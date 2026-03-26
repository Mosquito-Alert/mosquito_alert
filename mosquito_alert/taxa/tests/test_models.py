from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pytest
from unittest.mock import PropertyMock, patch

from ..models import Taxon


@pytest.mark.django_db
class TestTaxonModel:
    # classmethods
    def test_get_root_return_root_node(self, taxon_root):
        assert Taxon.get_root() == taxon_root

    def test_get_root_return_None_if_root_node_does_not_exist(self):
        Taxon.objects.all().delete()

        assert Taxon.get_root() is None

    def test_get_leaves_in_rank_group(self, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = genus.add_child(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = genus.add_child(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )
        species_1 = species_complex.add_child(
            name="species 1", rank=Taxon.TaxonomicRank.SPECIES
        )
        species_2 = species_complex.add_child(
            name="species 2", rank=Taxon.TaxonomicRank.SPECIES
        )

        assert frozenset(
            Taxon.get_leaves_in_rank_group(Taxon.TaxonomicRank.SPECIES_COMPLEX)
        ) == frozenset([species, species_1, species_2])
        assert frozenset(
            Taxon.get_leaves_in_rank_group(Taxon.TaxonomicRank.SPECIES)
        ) == frozenset([species, species_1, species_2])
        assert frozenset(
            Taxon.get_leaves_in_rank_group(Taxon.TaxonomicRank.GENUS)
        ) == frozenset([genus])

    # fields
    def test_rank_can_not_be_null(self):
        assert not Taxon._meta.get_field("rank").null

    def test_rank_can_not_be_blank(self):
        assert not Taxon._meta.get_field("rank").blank

    def test_name_can_not_be_null(self):
        assert not Taxon._meta.get_field("name").null

    def test_name_can_not_be_blank(self):
        assert not Taxon._meta.get_field("name").blank

    def test_name_max_length_is_32(self):
        assert Taxon._meta.get_field("name").max_length == 32

    def test_common_name_can_be_null(self):
        assert Taxon._meta.get_field("common_name").null

    def test_common_name_can_not_be_blank(self):
        assert Taxon._meta.get_field("common_name").blank

    def test_common_name_max_length_is_64(self):
        assert Taxon._meta.get_field("common_name").max_length == 64

    # properties
    def test_node_order_by_name(self):
        assert Taxon.node_order_by == ["name"]

    def test_is_specie_must_be_true_for_taxon_with_rank_species_complex_or_higher(self):
        obj = Taxon(rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)

        assert obj.is_specie

        obj.rank = Taxon.TaxonomicRank.SPECIES_COMPLEX.value - 1

        assert not obj.is_specie

    def test_prev_rank_group(self):
        genus = Taxon(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = Taxon(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = Taxon(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )

        assert genus.prev_rank_group == Taxon.TaxonomicRank.FAMILY
        assert species.prev_rank_group == Taxon.TaxonomicRank.GENUS
        assert species_complex.prev_rank_group == Taxon.TaxonomicRank.GENUS

    def test_next_rank_group(self):
        genus = Taxon(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        assert genus.next_rank_group == Taxon.TaxonomicRank.SPECIES_COMPLEX

    def test_rank_group(self):
        species = Taxon(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = Taxon(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )

        assert species.rank_group == Taxon.TaxonomicRank.SPECIES_COMPLEX
        assert species_complex.rank_group == Taxon.TaxonomicRank.SPECIES_COMPLEX

    # methods
    def test_get_leaves(self, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = genus.add_child(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = genus.add_child(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )
        species_1 = species_complex.add_child(
            name="species 1", rank=Taxon.TaxonomicRank.SPECIES
        )
        species_2 = species_complex.add_child(
            name="species 2", rank=Taxon.TaxonomicRank.SPECIES
        )

        assert frozenset(genus.get_leaves()) == frozenset(
            [species, species_1, species_2]
        )
        assert frozenset(species_complex.get_leaves()) == frozenset(
            [species_1, species_2]
        )

    def test_get_parent_in_prev_rank_group(self, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = genus.add_child(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = genus.add_child(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )
        species_1 = species_complex.add_child(
            name="species 1", rank=Taxon.TaxonomicRank.SPECIES
        )
        species_2 = species_complex.add_child(
            name="species 2", rank=Taxon.TaxonomicRank.SPECIES
        )

        # Regular parent
        assert species.get_parent_in_prev_rank_group() == genus
        assert species_complex.get_parent_in_prev_rank_group() == genus

        # Bypassing their parent, and going to previous rank group parent.
        assert species_1.get_parent_in_prev_rank_group() == genus
        assert species_2.get_parent_in_prev_rank_group() == genus

    def test_get_children_leaves_in_rank_group(self, taxon_root):
        genus = taxon_root.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = genus.add_child(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = genus.add_child(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )
        species_1 = species_complex.add_child(
            name="species 1", rank=Taxon.TaxonomicRank.SPECIES
        )
        species_2 = species_complex.add_child(
            name="species 2", rank=Taxon.TaxonomicRank.SPECIES
        )

        genus_1 = taxon_root.add_child(name="genus 1", rank=Taxon.TaxonomicRank.GENUS)
        species_1_1 = genus_1.add_child(
            name="species 1 1", rank=Taxon.TaxonomicRank.SPECIES
        )

        assert frozenset(genus.get_children_leaves_in_rank_group()) == frozenset(
            [species, species_1, species_2]
        )
        assert frozenset(genus_1.get_children_leaves_in_rank_group()) == frozenset(
            [species_1_1]
        )
        assert frozenset(
            species_complex.get_children_leaves_in_rank_group()
        ) == frozenset([])
        assert frozenset(species.get_children_leaves_in_rank_group()) == frozenset([])

    def test_get_sibling_leaves_in_rank_group(self, taxon_root):
        family = taxon_root.add_child(name="family", rank=Taxon.TaxonomicRank.FAMILY)
        genus = family.add_child(name="genus", rank=Taxon.TaxonomicRank.GENUS)
        species = genus.add_child(name="species", rank=Taxon.TaxonomicRank.SPECIES)
        species_complex = genus.add_child(
            name="species complex", rank=Taxon.TaxonomicRank.SPECIES_COMPLEX
        )
        species_1 = species_complex.add_child(
            name="species 1", rank=Taxon.TaxonomicRank.SPECIES
        )
        species_2 = species_complex.add_child(
            name="species 2", rank=Taxon.TaxonomicRank.SPECIES
        )

        genus_1 = family.add_child(name="genus 1", rank=Taxon.TaxonomicRank.GENUS)
        _ = genus_1.add_child(name="species 1 1", rank=Taxon.TaxonomicRank.SPECIES)

        assert frozenset(
            species_complex.get_sibling_leaves_in_rank_group()
        ) == frozenset([species])
        assert frozenset(species.get_sibling_leaves_in_rank_group()) == frozenset(
            [species_1, species_2]
        )

        assert frozenset(species_1.get_sibling_leaves_in_rank_group()) == frozenset(
            [species, species_2]
        )
        assert frozenset(species_2.get_sibling_leaves_in_rank_group()) == frozenset(
            [species, species_1]
        )

        assert frozenset(genus.get_sibling_leaves_in_rank_group()) == frozenset(
            [genus_1]
        )

    @pytest.mark.parametrize(
        "name, expected_result, is_specie",
        [
            ("dumMy StrangE nAme", "Dummy strange name", True),
            ("dumMy StrangE nAme", "dumMy StrangE nAme", False),
        ],
    )
    def test_name_is_capitalized_on_save_only_for_species(
        self, name, expected_result, is_specie, taxon_root
    ):
        with patch(
            f"{Taxon.__module__}.{Taxon.__name__}.is_specie", new_callable=PropertyMock
        ) as mocked_is_specie:
            mocked_is_specie.return_value = is_specie
            obj = taxon_root.add_child(name=name, rank=taxon_root.rank + 1)

            assert obj.name == expected_result

    def test_tree_is_ordered_by_name_on_parent_change(self, taxon_root):
        z_child = taxon_root.add_child(name="z", rank=Taxon.TaxonomicRank.GENUS)
        b_child = z_child.add_child(name="b", rank=Taxon.TaxonomicRank.SPECIES)
        a_child = taxon_root.add_child(name="a", rank=Taxon.TaxonomicRank.SPECIES)
        # NOTE: Need to refresh since last move changes the object.
        # See: https://django-treebeard.readthedocs.io/en/latest/caveats.html#raw-queries
        z_child.refresh_from_db()

        assert frozenset(Taxon.objects.all()) == frozenset(
            [taxon_root, a_child, z_child, b_child]
        )

        # Change parent
        a_child.move(z_child)

        assert frozenset(Taxon.objects.all()) == frozenset(
            [taxon_root, z_child, a_child, b_child]
        )

    def test_raise_when_rank_higher_than_parent_rank(self, taxon_root):
        taxon_specie = taxon_root.add_child(
            name="specie", rank=Taxon.TaxonomicRank.SPECIES
        )
        with pytest.raises(ValidationError):
            taxon_specie.add_child(rank=Taxon.TaxonomicRank.CLASS, name="class")

    # meta
    def test_unique_name_rank_constraint(self, taxon_root):
        taxon_root.add_child(
            name="Same Name",
            rank=Taxon.TaxonomicRank.SPECIES,
        )

        with pytest.raises(IntegrityError):
            # Create duplicate children name
            taxon_root.add_child(
                name="Same Name",
                rank=Taxon.TaxonomicRank.SPECIES,
            )

    def test_unique_root_constraint(self, taxon_root):
        with pytest.raises(IntegrityError):
            Taxon.add_root(name="", rank=taxon_root.rank)

    def test__str__(self, taxon_root):
        taxon = taxon_root.add_child(
            name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES
        )

        expected_result = "Aedes albopictus [Species]"
        assert taxon.__str__() == expected_result
