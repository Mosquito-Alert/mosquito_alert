from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import FieldDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.utils import DataError, IntegrityError

from mosquito_alert.geo.tests.factories import BoundaryFactory
from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import SpecieDistribution, Taxon
from .factories import SpecieDistributionFactory, TaxonFactory


@pytest.mark.django_db
class TestTaxonModel(BaseTestTimeStampedModel):
    model = Taxon
    factory_cls = TaxonFactory

    def test_get_root_return_root_node(self, taxon_root):
        assert Taxon.get_root() == taxon_root

    def test_get_root_return_None_if_root_node_does_not_exist(self):
        Taxon.objects.all().delete()

        assert Taxon.get_root() is None

    @pytest.mark.parametrize(
        "name, rank, expected_result",
        [
            ("Insecta", Taxon.TaxonomicRank.CLASS, "Insecta"),
            ("INSECTA", Taxon.TaxonomicRank.CLASS, "INSECTA"),
            ("DIptera", Taxon.TaxonomicRank.ORDER, "DIptera"),
            ("GenUs", Taxon.TaxonomicRank.GENUS, "GenUs"),
            ("Anopheles Gambiae Sensu Lato", Taxon.TaxonomicRank.SPECIES_COMPLEX, "Anopheles gambiae sensu lato"),
            ("Aedes Albopictus", Taxon.TaxonomicRank.SPECIES, "Aedes albopictus"),
            ("Aedes albopictus", Taxon.TaxonomicRank.SPECIES, "Aedes albopictus"),
            ("AEDES ALBOPICTUS", Taxon.TaxonomicRank.SPECIES, "Aedes albopictus"),
        ],
    )
    def test_name_is_capitalized_when_is_rank_specie(self, name, rank, expected_result):
        taxon = self.factory_cls(name=name, rank=rank)
        assert taxon.name == expected_result

        taxon.name = ""
        taxon.save()

        # On change name
        taxon.name = name
        taxon.save()
        assert taxon.name == expected_result

    def test_name_is_not_capitalized_when_not_species(self):
        taxon = self.factory_cls(name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES)
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
        taxon = self.factory_cls(rank=rank)
        assert taxon.is_specie == expected_result

    def test__str__(self, taxon_root):
        taxon = self.factory_cls(name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)

        expected_result = "Aedes albopictus [Species]"
        assert taxon.__str__() == expected_result

    def test_raise_when_rank_higher_than_parent_rank(self, taxon_specie):
        with pytest.raises(ValueError):
            _ = self.factory_cls(rank=Taxon.TaxonomicRank.CLASS, parent=taxon_specie)

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
            self.factory_cls(parent=None, name="", rank=taxon_root.rank)

    def test_null_common_name_is_allowed(self, taxon_root):
        self.factory_cls(common_name=None, parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)

    def test_null_name_is_not_allowed_on_change(self, taxon_specie):
        taxon_specie.name = None

        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            taxon_specie.save()

    def test_null_name_is_not_allowed_on_create(self, taxon_root):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            self.factory_cls(name=None, parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)

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
                self.factory_cls(name=name, rank=Taxon.TaxonomicRank.SPECIES)
        else:
            self.factory_cls(name=name, rank=Taxon.TaxonomicRank.SPECIES)

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
                self.factory_cls(common_name=common_name, rank=Taxon.TaxonomicRank.SPECIES)
        else:
            self.factory_cls(common_name=common_name, rank=Taxon.TaxonomicRank.SPECIES)

    def test_tree_is_ordered_by_name_on_create(self, taxon_root):
        z_child = self.factory_cls(name="z", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)
        a_child = self.factory_cls(name="a", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)

        assert frozenset(Taxon.objects.all()) == frozenset([taxon_root, a_child, z_child])

    def test_tree_is_ordered_by_name_on_parent_change(self, taxon_root):
        z_child = self.factory_cls(name="z", rank=Taxon.TaxonomicRank.GENUS, parent=taxon_root)
        b_child = self.factory_cls(name="b", rank=Taxon.TaxonomicRank.SPECIES, parent=z_child)
        a_child = self.factory_cls(name="a", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)
        # NOTE: Need to refresh since last move changes the object.
        # See: https://django-treebeard.readthedocs.io/en/latest/caveats.html#raw-queries
        z_child.refresh_from_db()

        assert frozenset(Taxon.objects.all()) == frozenset([taxon_root, a_child, z_child, b_child])

        a_child.parent = z_child
        a_child.save()

        assert frozenset(Taxon.objects.all()) == frozenset([taxon_root, z_child, a_child, b_child])

    def test_gbif_id_can_be_null(self):
        assert Taxon._meta.get_field("gbif_id").null

    def test_gbif_id_can_be_blank(self):
        assert Taxon._meta.get_field("gbif_id").blank

    # properties
    @pytest.mark.parametrize("gbif_id, expected_result", [(None, ""), (12345, "https://www.gbif.org/species/12345")])
    def test_gbif_url(self, gbif_id, expected_result):
        assert self.factory_cls(gbif_id=gbif_id).gbif_url == expected_result


@pytest.mark.django_db
class TestSpecieDistributionModel:
    def test_boundary_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            SpecieDistributionFactory(boundary=None)

    def test_boundary_is_protected_on_delete(self):
        sd = SpecieDistributionFactory()

        with pytest.raises(ProtectedError):
            sd.boundary.delete()

    def test_taxon_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            SpecieDistributionFactory(taxon=None)

    def test_taxon_is_protected_on_delete(self):
        sd = SpecieDistributionFactory()

        with pytest.raises(ProtectedError):
            sd.taxon.delete()

    @pytest.mark.parametrize(
        "taxon_rank, expected_raise",
        [
            (Taxon.TaxonomicRank.DOMAIN, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.KINGDOM, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.PHYLUM, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.CLASS, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.ORDER, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.FAMILY, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.GENUS, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.SUBGENUS, pytest.raises(ValueError)),
            (Taxon.TaxonomicRank.SPECIES_COMPLEX, does_not_raise()),
            (Taxon.TaxonomicRank.SPECIES, does_not_raise()),
        ],
    )
    def test_taxon_is_allowed_to_be_species_only(self, taxon_rank, expected_raise):
        with expected_raise:
            assert SpecieDistributionFactory(taxon__rank=taxon_rank)

    def test_taxon_related_name_is_distribution(self):
        sd = SpecieDistributionFactory()

        assert frozenset(sd.taxon.distribution.all()) == frozenset([sd])

    @pytest.mark.parametrize(
        "fieldname, expected_raise",
        [
            ("boundary", pytest.raises(FieldDoesNotExist)),
            ("taxon", pytest.raises(FieldDoesNotExist)),
            ("source", pytest.raises(FieldDoesNotExist)),
            ("status", does_not_raise()),
        ],
    )
    def test_monitored_changes_in_fields(self, fieldname, expected_raise):
        with expected_raise:
            SpecieDistribution.history.model._meta.get_field(fieldname)

    def test_new_history_record_is_created_on_status_change(self):
        sd = SpecieDistributionFactory(status=SpecieDistribution.DistributionStatus.ABSENT)

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

        assert sd.history.last().status == SpecieDistribution.DistributionStatus.ABSENT

        sd.status = SpecieDistribution.DistributionStatus.REPORTED
        sd.save()

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 2

        assert sd.history.first().history_type == "~"
        assert sd.history.first().status == SpecieDistribution.DistributionStatus.REPORTED

    def test_no_history_record_created_if_status_is_not_changed(self, country_bl, taxon_root):
        sd = SpecieDistributionFactory(
            boundary__boundary_layer=country_bl,
            taxon=TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES),
            source=SpecieDistribution.DataSource.SELF,
        )

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

        sd.boundary = BoundaryFactory(boundary_layer=country_bl)
        sd.save()

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

        sd.taxon = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)
        sd.save()

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

        sd.source = SpecieDistribution.DataSource.ECDC
        sd.save()

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

    def test_historic_record_type_is_created_on_creation(self):
        sd = SpecieDistributionFactory()

        assert sd.history.first().history_type == "+"

    def test_historical_records_are_deleted_on_master_deletion(self):
        sd = SpecieDistributionFactory(status=SpecieDistribution.DistributionStatus.ABSENT)

        assert SpecieDistribution.objects.all().count() == 1
        assert SpecieDistribution.history.all().count() == 1

        sd.delete()

        assert SpecieDistribution.objects.all().count() == 0
        assert SpecieDistribution.history.all().count() == 0

    def test_unique_contraint_boundary_taxon_source(self):
        sd = SpecieDistributionFactory()

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = SpecieDistributionFactory(boundary=sd.boundary, taxon=sd.taxon, source=sd.source)
