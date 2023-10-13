from contextlib import nullcontext as does_not_raise
from unittest.mock import PropertyMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError

from mosquito_alert.geo.tests.factories import BoundaryFactory
from mosquito_alert.utils.tests.test_models import BaseTestTimeStampedModel

from ..models import SpecieDistribution, Taxon
from .factories import SpecieDistributionFactory, TaxonFactory


@pytest.mark.django_db
class TestTaxonModel(BaseTestTimeStampedModel):
    model = Taxon
    factory_cls = TaxonFactory

    # classmethods
    def test_get_root_return_root_node(self, taxon_root):
        assert self.model.get_root() == taxon_root

    def test_get_root_return_None_if_root_node_does_not_exist(self):
        self.model.objects.all().delete()

        assert self.model.get_root() is None

    # fields
    def test_rank_can_not_be_null(self):
        assert not self.model._meta.get_field("rank").null

    def test_rank_can_not_be_blank(self):
        assert not self.model._meta.get_field("rank").blank

    def test_name_can_not_be_null(self):
        assert not self.model._meta.get_field("name").null

    def test_name_can_not_be_blank(self):
        assert not self.model._meta.get_field("name").blank

    def test_name_max_length_is_32(self):
        assert self.model._meta.get_field("name").max_length == 32

    def test_common_name_can_be_null(self):
        assert self.model._meta.get_field("common_name").null

    def test_common_name_can_not_be_blank(self):
        assert self.model._meta.get_field("common_name").blank

    def test_common_name_max_length_is_64(self):
        assert self.model._meta.get_field("common_name").max_length == 64

    def test_gbif_id_can_be_null(self):
        assert self.model._meta.get_field("gbif_id").null

    def test_gbif_id_can_be_blank(self):
        assert self.model._meta.get_field("gbif_id").blank

    def test_gbif_id_is_unique(self):
        assert self.model._meta.get_field("gbif_id").unique

    # properties
    def test_node_order_by_name(self):
        assert self.model.node_order_by == ["name"]

    @pytest.mark.parametrize("gbif_id, expected_result", [(None, ""), (12345, "https://www.gbif.org/species/12345")])
    def test_gbif_url(self, gbif_id, expected_result):
        assert self.factory_cls(gbif_id=gbif_id).gbif_url == expected_result

    def test_is_specie_must_be_true_for_taxon_with_rank_species_complex_or_higher(self):
        obj = self.factory_cls.build(rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)

        assert obj.is_specie

        obj.rank = Taxon.TaxonomicRank.SPECIES_COMPLEX.value - 1

        assert not obj.is_specie

    # methods
    @pytest.mark.parametrize(
        "name, expected_result, is_specie",
        [
            ("dumMy StrangE nAme", "Dummy strange name", True),
            ("dumMy StrangE nAme", "dumMy StrangE nAme", False),
        ],
    )
    def test_name_is_capitalized_on_save_only_for_species(self, name, expected_result, is_specie):
        with patch(
            f"{self.model.__module__}.{self.model.__name__}.is_specie", new_callable=PropertyMock
        ) as mocked_is_specie:
            mocked_is_specie.return_value = is_specie
            obj = self.factory_cls(name=name)

            assert obj.name == expected_result

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

    def test_raise_when_rank_higher_than_parent_rank(self, taxon_specie):
        with pytest.raises(ValidationError):
            _ = self.factory_cls(rank=Taxon.TaxonomicRank.CLASS, parent=taxon_specie)

    # meta
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

    def test__str__(self, taxon_root):
        taxon = self.factory_cls(name="Aedes Albopictus", rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_root)

        expected_result = "Aedes albopictus [Species]"
        assert taxon.__str__() == expected_result


@pytest.mark.django_db
class TestSpecieDistributionModel(BaseTestTimeStampedModel):
    model = SpecieDistribution
    factory_cls = SpecieDistributionFactory

    # fields
    def test_boundary_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary").null

    def test_boundary_can_not_be_blank(self):
        assert not self.model._meta.get_field("boundary").blank

    def test_boundary_is_protected_on_delete(self):
        _on_delete = self.model._meta.get_field("boundary").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_boundary_related_name(self):
        assert self.model._meta.get_field("boundary").remote_field.related_name == "+"

    def test_taxon_can_not_be_null(self):
        assert not self.model._meta.get_field("taxon").null

    def test_taxon_can_not_be_blank(self):
        assert not self.model._meta.get_field("taxon").blank

    def test_taxon_is_protected_on_delete(self):
        _on_delete = self.model._meta.get_field("taxon").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_taxon_related_name(self):
        assert self.model._meta.get_field("taxon").remote_field.related_name == "distribution"

    def test_source_can_not_be_null(self):
        assert not self.model._meta.get_field("source").null

    def test_source_can_not_be_blank(self):
        assert not self.model._meta.get_field("source").blank

    def test_status_can_not_be_null(self):
        assert not self.model._meta.get_field("status").null

    def test_status_can_not_be_blank(self):
        assert not self.model._meta.get_field("status").blank

    # properties
    def test_history_only_tracks_status(self):
        assert self.model.history.model.history_object.fields_included == [
            self.model._meta.get_field("id"),
            self.model._meta.get_field("status"),
        ]

    @pytest.mark.parametrize(
        "is_specie, expected_raise",
        [
            (True, does_not_raise()),
            (False, pytest.raises(ValueError)),
        ],
    )
    def test_taxon_is_allowed_to_be_species_only(self, is_specie, expected_raise):
        with patch(f"{Taxon.__module__}.{Taxon.__name__}.is_specie", new_callable=PropertyMock) as mocked_is_specie:
            mocked_is_specie.return_value = is_specie
            with expected_raise:
                _ = self.factory_cls()

    def test_new_history_record_is_created_on_status_change(self):
        sd = self.factory_cls(status=SpecieDistribution.DistributionStatus.ABSENT)

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        assert sd.history.last().status == SpecieDistribution.DistributionStatus.ABSENT

        sd.status = SpecieDistribution.DistributionStatus.REPORTED
        sd.save()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 2

        assert sd.history.first().history_type == "~"
        assert sd.history.first().status == SpecieDistribution.DistributionStatus.REPORTED

    def test_no_history_record_created_if_status_is_not_changed(self, country_bl, taxon_root):
        sd = self.factory_cls(
            boundary__boundary_layer=country_bl,
            taxon=TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES),
            source=SpecieDistribution.DataSource.SELF,
        )

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        sd.boundary = BoundaryFactory(boundary_layer=country_bl)
        sd.save()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        sd.taxon = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)
        sd.save()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        sd.source = SpecieDistribution.DataSource.ECDC
        sd.save()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

    def test_historic_record_type_is_created_on_creation(self):
        sd = self.factory_cls()

        assert sd.history.first().history_type == "+"

    def test_historical_records_are_deleted_on_master_deletion(self):
        sd = self.factory_cls(status=SpecieDistribution.DistributionStatus.ABSENT)

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        sd.delete()

        assert self.model.objects.all().count() == 0
        assert self.model.history.all().count() == 0

    # meta

    def test_unique_contraint_boundary_taxon_source(self):
        sd = self.factory_cls()

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = self.factory_cls(boundary=sd.boundary, taxon=sd.taxon, source=sd.source)
