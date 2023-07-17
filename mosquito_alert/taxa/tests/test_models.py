import pytest
from django.db.utils import DataError, IntegrityError

from ..models import Taxon
from .factories import TaxonFactory


@pytest.mark.django_db
class TestTaxonModel:
    def test_name_is_capitalized(self):
        taxon = TaxonFactory(name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES)
        assert taxon.name == "Aedes albopictus"

        # On change name
        taxon.name = "AEDES ALBOPICTUS"
        taxon.save()
        assert taxon.name == "Aedes albopictus"

    @pytest.mark.parametrize(
        "rank, expected_result",
        [
            (Taxon.TaxonomicRank.CLASS, False),
            (Taxon.TaxonomicRank.SUBGENUS, False),
            (Taxon.TaxonomicRank.SPECIES, True),
            (Taxon.TaxonomicRank.SPECIES_COMPLEX, True),
        ],
    )
    def test_is_species_property(self, rank, expected_result):
        taxon = TaxonFactory(rank=rank)
        assert taxon.is_specie == expected_result

    def test__str__(self, taxon_root):
        taxon = TaxonFactory(
            name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root
        )

        expected_result = "Aedes albopictus [Species]"
        assert taxon.__str__() == expected_result

    def test_raise_when_rank_higher_than_parent_rank(self, taxon_specie):
        with pytest.raises(ValueError):
            _ = TaxonFactory(rank=Taxon.TaxonomicRank.CLASS, parent=taxon_specie)

    def test_unique_name_rank_constraint(self, taxon_root):
        with pytest.raises(IntegrityError):
            # Create duplicate children name
            _ = TaxonFactory.create_batch(
                2,
                name="Same Name",
                rank=Taxon.TaxonomicRank.SPECIES,
                parent=taxon_root,
            )

    def test_unique_root_constraint(self, taxon_root):
        with pytest.raises(IntegrityError):
            TaxonFactory(name="", rank=taxon_root.rank)

    def test_null_common_name_is_allowed(self, taxon_root):
        TaxonFactory(
            common_name=None, parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES
        )

    def test_null_name_is_not_allowed_on_change(self, taxon_specie):
        taxon_specie.name = None

        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            taxon_specie.save()

    def test_null_name_is_not_allowed_on_create(self, taxon_root):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            TaxonFactory(name=None, parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)

    @pytest.mark.parametrize(
        "name, output_raises",
        [
            ("a" * 31, False),
            ("a" * 32, False),
            ("a" * 33, True),
        ],
    )
    def test_name_max_length_is_32(self, name, output_raises):
        if output_raises:
            with pytest.raises(DataError):
                TaxonFactory(name=name, rank=Taxon.TaxonomicRank.SPECIES)
        else:
            TaxonFactory(name=name, rank=Taxon.TaxonomicRank.SPECIES)

    @pytest.mark.parametrize(
        "common_name, output_raises",
        [
            ("a" * 63, False),
            ("a" * 64, False),
            ("a" * 65, True),
        ],
    )
    def test_common_name_max_length_is_64(self, common_name, output_raises):
        if output_raises:
            with pytest.raises(DataError):
                TaxonFactory(common_name=common_name, rank=Taxon.TaxonomicRank.SPECIES)
        else:
            TaxonFactory(common_name=common_name, rank=Taxon.TaxonomicRank.SPECIES)

    def test_tree_is_ordered_by_name_on_create(self, taxon_root):
        z_child = TaxonFactory(
            name="z", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root
        )
        a_child = TaxonFactory(
            name="a", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root
        )

        assert frozenset(Taxon.objects.all()) == frozenset(
            [taxon_root, a_child, z_child]
        )

    def test_tree_is_ordered_by_name_on_parent_change(self, taxon_root):
        z_child = TaxonFactory(
            name="z", rank=Taxon.TaxonomicRank.GENUS, parent=taxon_root
        )
        b_child = TaxonFactory(
            name="b", rank=Taxon.TaxonomicRank.SPECIES, parent=z_child
        )
        a_child = TaxonFactory(
            name="a", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root
        )
        # NOTE: Need to refresh since last move changes the object.
        # See: https://django-treebeard.readthedocs.io/en/latest/caveats.html#raw-queries
        z_child.refresh_from_db()

        assert frozenset(Taxon.objects.all()) == frozenset(
            [taxon_root, a_child, z_child, b_child]
        )

        a_child.parent = z_child
        a_child.save()

        assert frozenset(Taxon.objects.all()) == frozenset(
            [taxon_root, z_child, a_child, b_child]
        )
