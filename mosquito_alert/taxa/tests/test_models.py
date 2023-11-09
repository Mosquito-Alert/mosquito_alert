from contextlib import nullcontext as does_not_raise
from datetime import datetime, timedelta
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone
from django_lifecycle import AFTER_CREATE, AFTER_UPDATE, BEFORE_CREATE, hook
from django_mock_queries.query import MockSet

from mosquito_alert.geo.tests.factories import BoundaryFactory, BoundaryLayerFactory
from mosquito_alert.individuals.tests.factories import IndividualFactory
from mosquito_alert.reports.tests.factories import IndividualReportFactory
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

    # classmethod
    def test_update_for_calls_get_or_create_only_for_leaves(self, taxon_root, country_bl):
        # NOTE: adding name to force ordering.
        t_child = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.GENUS)
        t_spec_complex = TaxonFactory(parent=t_child, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_leaf1 = TaxonFactory(name="A", parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)
        t_leaf2 = TaxonFactory(name="Z", parent=t_child, rank=Taxon.TaxonomicRank.SPECIES)

        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_child = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child = BoundaryFactory(parent=b_root, boundary_layer=bl_child)

        bl_leaf = BoundaryLayerFactory(parent=bl_child, boundary_type=bl_child.boundary_type)
        b_leaf1 = BoundaryFactory(name="A", parent=b_child, boundary_layer=bl_leaf)
        b_leaf2 = BoundaryFactory(name="Z", parent=b_child, boundary_layer=bl_leaf)

        # Test on create
        with patch(
            f"{SpecieDistribution.__module__}.{SpecieDistribution.__name__}.objects.get_or_create",
            return_value=(object, True),
        ) as mock_get_or_create:
            SpecieDistribution.update_for(boundary=b_root, taxon=taxon_root)

            assert mock_get_or_create.call_args_list == [
                call(boundary=b_leaf1, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF),
                call(boundary=b_leaf1, taxon=t_leaf2, source=SpecieDistribution.DataSource.SELF),
                call(boundary=b_leaf2, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF),
                call(boundary=b_leaf2, taxon=t_leaf2, source=SpecieDistribution.DataSource.SELF),
            ]

    def test_update_for_calls_update_if_object_already_exist(self, taxon_specie, country_bl):
        boundary_obj = BoundaryFactory(boundary_layer=country_bl)

        mocked_obj = MagicMock()
        with patch(
            f"{SpecieDistribution.__module__}.{SpecieDistribution.__name__}.objects.get_or_create",
            return_value=(mocked_obj, False),
        ):
            SpecieDistribution.update_for(boundary=boundary_obj, taxon=taxon_specie, from_datetime="DUMMY DATETIME")

            mocked_obj.update.assert_called_once_with(from_datetime="DUMMY DATETIME")

    # fields
    def test_boundary_limit_choices_to_is_leaves(self):
        assert self.model._meta.get_field("boundary").remote_field.limit_choices_to == {"numchild": 0}

    def test_boundary_can_not_be_null(self):
        assert not self.model._meta.get_field("boundary").null

    def test_boundary_can_not_be_blank(self):
        assert not self.model._meta.get_field("boundary").blank

    def test_boundary_is_protected_on_delete(self):
        _on_delete = self.model._meta.get_field("boundary").remote_field.on_delete
        assert _on_delete == models.PROTECT

    def test_boundary_related_name(self):
        assert self.model._meta.get_field("boundary").remote_field.related_name == "+"

    def test_taxon_limit_choices_to_is_gt_species_complex(self):
        assert self.model._meta.get_field("taxon").remote_field.limit_choices_to == {
            "rank__gte": Taxon.TaxonomicRank.SPECIES_COMPLEX
        }

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

    def test_status_can_be_null(self):
        assert self.model._meta.get_field("status").null

    def test_status_can_be_blank(self):
        assert self.model._meta.get_field("status").blank

    def test_status_since_default_is_now(self):
        assert self.model._meta.get_field("status_since").default == timezone.now

    def test_status_since_can_be_blank(self):
        assert self.model._meta.get_field("status_since").blank

    def test_status_since_is_not_editable(self):
        assert not self.model._meta.get_field("status_since").editable

    def test_stats_summary_can_be_null(self):
        assert self.model._meta.get_field("stats_summary").null

    def test_stats_summary_can_be_blank(self):
        assert self.model._meta.get_field("stats_summary").blank

    def test_stats_summary_is_not_editable(self):
        assert not self.model._meta.get_field("stats_summary").editable

    # objects
    def test_objects_get_tree_for_instance(self, taxon_root, country_bl):
        t_child = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.GENUS)
        t_spec_complex = TaxonFactory(parent=t_child, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_leaf1 = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_child = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child = BoundaryFactory(parent=b_root, boundary_layer=bl_child)

        bl_leaf = BoundaryLayerFactory(parent=bl_child, boundary_type=bl_child.boundary_type)
        b_leaf1 = BoundaryFactory(parent=b_child, boundary_layer=bl_leaf)

        sd_obj = self.factory_cls(boundary=b_leaf1, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF)

        sd_b_root_t_complex = self.model.objects.get(boundary=b_root, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_root_t_leaf = self.model.objects.get(boundary=b_root, taxon=t_leaf1, source=sd_obj.source)
        sd_b_child_t_complex = self.model.objects.get(boundary=b_child, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_child_t_leaf = self.model.objects.get(boundary=b_child, taxon=t_leaf1, source=sd_obj.source)
        sd_b_leaf1_t_complex = self.model.objects.get(boundary=b_leaf1, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_leaf1_t_leaf = self.model.objects.get(boundary=b_leaf1, taxon=t_leaf1, source=sd_obj.source)

        # Without including taxon descendants
        assert frozenset(
            self.model.objects.get_tree_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=False)
        ) == frozenset([sd_b_root_t_complex, sd_b_child_t_complex, sd_b_leaf1_t_complex])

        # Including taxon descendants
        assert frozenset(
            self.model.objects.get_tree_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=True)
        ) == frozenset(
            [
                sd_b_root_t_complex,
                sd_b_root_t_leaf,
                sd_b_child_t_complex,
                sd_b_child_t_leaf,
                sd_b_leaf1_t_complex,
                sd_b_leaf1_t_leaf,
            ]
        )

    def test_objects_get_descendants_for_instance(self, taxon_root, country_bl):
        t_child = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.GENUS)
        t_spec_complex = TaxonFactory(parent=t_child, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_leaf1 = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_child = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child = BoundaryFactory(parent=b_root, boundary_layer=bl_child)

        bl_leaf = BoundaryLayerFactory(parent=bl_child, boundary_type=bl_child.boundary_type)
        b_leaf1 = BoundaryFactory(parent=b_child, boundary_layer=bl_leaf)

        sd_obj = self.factory_cls(boundary=b_leaf1, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF)

        sd_b_root_t_complex = self.model.objects.get(boundary=b_root, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_root_t_leaf = self.model.objects.get(boundary=b_root, taxon=t_leaf1, source=sd_obj.source)
        sd_b_child_t_complex = self.model.objects.get(boundary=b_child, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_child_t_leaf = self.model.objects.get(boundary=b_child, taxon=t_leaf1, source=sd_obj.source)
        sd_b_leaf1_t_complex = self.model.objects.get(boundary=b_leaf1, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_leaf1_t_leaf = self.model.objects.get(boundary=b_leaf1, taxon=t_leaf1, source=sd_obj.source)

        # Without including taxon descendants
        assert frozenset(
            self.model.objects.get_descendants_for_instance(
                instance=sd_b_root_t_complex, include_taxon_descendants=False
            )
        ) == frozenset([sd_b_child_t_complex, sd_b_leaf1_t_complex])

        # Including taxon descendants
        assert frozenset(
            self.model.objects.get_descendants_for_instance(
                instance=sd_b_root_t_complex, include_taxon_descendants=True
            )
        ) == frozenset(
            [
                sd_b_root_t_leaf,
                sd_b_child_t_complex,
                sd_b_child_t_leaf,
                sd_b_leaf1_t_complex,
                sd_b_leaf1_t_leaf,
            ]
        )

    def test_objects_get_children_for_instance(self, taxon_root, country_bl):
        t_child = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.GENUS)
        t_spec_complex = TaxonFactory(parent=t_child, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_leaf1 = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_child = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child = BoundaryFactory(parent=b_root, boundary_layer=bl_child)

        bl_leaf = BoundaryLayerFactory(parent=bl_child, boundary_type=bl_child.boundary_type)
        b_leaf1 = BoundaryFactory(parent=b_child, boundary_layer=bl_leaf)

        sd_obj = self.factory_cls(boundary=b_leaf1, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF)

        sd_b_root_t_complex = self.model.objects.get(boundary=b_root, taxon=t_spec_complex, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_root, taxon=t_leaf1, source=sd_obj.source)
        sd_b_child_t_complex = self.model.objects.get(boundary=b_child, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_child_t_leaf = self.model.objects.get(boundary=b_child, taxon=t_leaf1, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_leaf1, taxon=t_spec_complex, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_leaf1, taxon=t_leaf1, source=sd_obj.source)

        # Without including taxon descendants
        assert frozenset(
            self.model.objects.get_children_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=False)
        ) == frozenset([sd_b_child_t_complex])

        # Including taxon descendants
        assert frozenset(
            self.model.objects.get_children_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=True)
        ) == frozenset(
            [
                sd_b_child_t_complex,
                sd_b_child_t_leaf,
            ]
        )

    def test_objects_get_leaves_for_instance(self, taxon_root, country_bl):
        t_child = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.GENUS)
        t_spec_complex = TaxonFactory(parent=t_child, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_leaf1 = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_child = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child = BoundaryFactory(parent=b_root, boundary_layer=bl_child)

        bl_leaf = BoundaryLayerFactory(parent=bl_child, boundary_type=bl_child.boundary_type)
        b_leaf1 = BoundaryFactory(parent=b_child, boundary_layer=bl_leaf)

        sd_obj = self.factory_cls(boundary=b_leaf1, taxon=t_leaf1, source=SpecieDistribution.DataSource.SELF)

        sd_b_root_t_complex = self.model.objects.get(boundary=b_root, taxon=t_spec_complex, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_root, taxon=t_leaf1, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_child, taxon=t_spec_complex, source=sd_obj.source)
        _ = self.model.objects.get(boundary=b_child, taxon=t_leaf1, source=sd_obj.source)
        sd_b_leaf1_t_complex = self.model.objects.get(boundary=b_leaf1, taxon=t_spec_complex, source=sd_obj.source)
        sd_b_leaf1_t_leaf = self.model.objects.get(boundary=b_leaf1, taxon=t_leaf1, source=sd_obj.source)

        # Without including taxon descendants
        assert frozenset(
            self.model.objects.get_leaves_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=False)
        ) == frozenset([sd_b_leaf1_t_complex])

        # Including taxon descendants
        assert frozenset(
            self.model.objects.get_leaves_for_instance(instance=sd_b_root_t_complex, include_taxon_descendants=True)
        ) == frozenset(
            [
                sd_b_leaf1_t_complex,
                sd_b_leaf1_t_leaf,
            ]
        )

    # properties
    def test_history_only_tracks_status_and_stats_summary(self):
        assert self.model.history.model.history_object.fields_included == [
            self.model._meta.get_field("id"),
            self.model._meta.get_field("status"),
            self.model._meta.get_field("stats_summary"),
        ]

    @pytest.mark.parametrize(
        "source, expected_result", [(SpecieDistribution.DataSource.SELF, True), ("OTHER VALUES", False)]
    )
    def test_is_source_self_is_true_only_when_self(self, source, expected_result):
        obj = self.factory_cls.build(source=source)
        assert obj.is_source_self is expected_result

    def test_pretty_stats_summary(self):
        obj = self.factory_cls.build()
        obj.stats_summary = {
            SpecieDistribution.DistributionStatus.ABSENT.value: {"count": 1, "percentage": 100},
            -1: {"count": 0, "percentage": 0},
        }

        assert obj.pretty_stats_summary == {
            SpecieDistribution.DistributionStatus.ABSENT.label: {"count": 1, "percentage": 100},
            -1: {"count": 0, "percentage": 0},
        }

    # methods
    def test__get_status_changes_from_reports(self, taxon_root, country_bl):
        boundary = BoundaryFactory(boundary_layer=country_bl, with_geometry=True)
        point = boundary.geometry.point_on_surface

        t_spec_complex = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_spec = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        # Getting status changes for taxon complex now should be empty
        sd_b_t_complex = self.factory_cls.build(taxon=t_spec_complex, boundary=boundary)
        sd_b_t_species = self.factory_cls.build(taxon=t_spec, boundary=boundary)
        assert sd_b_t_complex._get_status_changes_from_reports() == []
        assert sd_b_t_species._get_status_changes_from_reports() == []

        # First taxon complex report
        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2022-11-04T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec_complex)],
        )

        # First taxon species report
        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2022-11-05T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec)],
        )

        # Next taxon species reports
        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2022-11-06T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec)],
        )

        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2022-11-07T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec)],
        )

        # This is not browsable (unpublished)
        _ = IndividualReportFactory(
            published=False,
            observed_at=datetime.fromisoformat("2022-11-08T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec)],
        )

        # Next year
        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2023-01-01T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec_complex)],
        )

        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2023-01-03T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=t_spec)],
        )

        # Getting status changes for taxon complex
        assert sd_b_t_complex._get_status_changes_from_reports() == [
            (datetime.fromisoformat("2022-11-04T00:05:00Z"), SpecieDistribution.DistributionStatus.REPORTED),
            (datetime.fromisoformat("2022-11-07T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
            (datetime.fromisoformat("2023-01-01T00:05:00Z"), SpecieDistribution.DistributionStatus.ESTABLISHED),
        ]

        assert sd_b_t_complex._get_status_changes_from_reports(
            from_datetime=datetime.fromisoformat("2022-11-05T00:05:00Z"),
            to_datetime=datetime.fromisoformat("2022-11-07T01:05:00Z"),
        ) == [
            (datetime.fromisoformat("2022-11-07T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
        ]

        # Getting status changes for taxon species
        assert sd_b_t_species._get_status_changes_from_reports() == [
            (datetime.fromisoformat("2022-11-05T00:05:00Z"), SpecieDistribution.DistributionStatus.REPORTED),
            (datetime.fromisoformat("2023-01-03T00:05:00Z"), SpecieDistribution.DistributionStatus.ESTABLISHED),
        ]

    def test__get_status_changes_from_children(self, country_bl, taxon_root, freezer):
        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_province = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child1 = BoundaryFactory(parent=b_root, boundary_layer=bl_province)
        b_child2 = BoundaryFactory(parent=b_root, boundary_layer=bl_province)

        t_spec_complex = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_spec = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        list_create_species_distribution = [
            (
                datetime.fromisoformat("2022-11-04T00:05:00Z"),
                dict(
                    boundary=b_child1,
                    taxon=t_spec_complex,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.REPORTED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-05T00:05:00Z"),
                dict(
                    boundary=b_child1,
                    taxon=t_spec,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.INTRODUCED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-06T00:05:00Z"),
                dict(
                    boundary=b_child2,
                    taxon=t_spec_complex,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.ESTABLISHED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-07T00:05:00Z"),
                dict(
                    boundary=b_child2,
                    taxon=t_spec,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.REPORTED,
                ),
            ),
        ]

        for timestamp, create_kwargs in list_create_species_distribution:
            freezer.move_to(timestamp)
            _obj = self.factory_cls.build(**create_kwargs)
            _obj.save(skip_hooks=True)

        # Getting status changes for taxon complex
        sd_b_root_t_complex = self.factory_cls.build(
            boundary=b_root, taxon=t_spec_complex, source=SpecieDistribution.DataSource.SELF
        )
        assert sd_b_root_t_complex._get_status_changes_from_children() == [
            (datetime.fromisoformat("2022-11-04T00:05:00Z"), SpecieDistribution.DistributionStatus.REPORTED),
            (datetime.fromisoformat("2022-11-05T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
            (datetime.fromisoformat("2022-11-06T00:05:00Z"), SpecieDistribution.DistributionStatus.ESTABLISHED),
        ]

        assert sd_b_root_t_complex._get_status_changes_from_children(
            from_datetime=datetime.fromisoformat("2022-11-05T01:05:00Z"),
            to_datetime=datetime.fromisoformat("2022-11-07T01:05:00Z"),
        ) == [
            (datetime.fromisoformat("2022-11-06T00:05:00Z"), SpecieDistribution.DistributionStatus.ESTABLISHED),
        ]

        # Getting status changes for taxon species
        sd_b_root_t_specie = self.factory_cls.build(
            boundary=b_root, taxon=t_spec, source=SpecieDistribution.DataSource.SELF
        )
        assert sd_b_root_t_specie._get_status_changes_from_children() == [
            (datetime.fromisoformat("2022-11-05T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
        ]

    def test_get_status_changes_returns_empty_list_is_is_not_source_self(self):
        obj = self.factory_cls.build(source="DUMMY SOURCE")

        assert obj.get_status_changes() == []

    def test_get_status_changes_calls_get_from_reports_if_is_leaf(self):
        obj = self.factory_cls.build(source=SpecieDistribution.DataSource.SELF)

        with patch.object(obj.boundary, "is_leaf", return_value=True):
            with patch.object(obj, "_get_status_changes_from_reports", return_value="DUMMY RETURN") as mocked_method:
                returned_value = obj.get_status_changes(from_datetime="from_datetime", to_datetime="to_datetime")

                mocked_method.assert_called_once_with(from_datetime="from_datetime", to_datetime="to_datetime")
                assert returned_value == "DUMMY RETURN"

    def test_get_status_changes_calls_get_from_children_if_not_leaf(self):
        obj = self.factory_cls.build(source=SpecieDistribution.DataSource.SELF)

        with patch.object(obj.boundary, "is_leaf", return_value=False):
            with patch.object(obj, "_get_status_changes_from_children", return_value="DUMMY RETURN") as mocked_method:
                returned_value = obj.get_status_changes(from_datetime="from_datetime", to_datetime="to_datetime")

                mocked_method.assert_called_once_with(from_datetime="from_datetime", to_datetime="to_datetime")
                assert returned_value == "DUMMY RETURN"

    def test_get_stats_summary_changes_return_empty_list_if_not_source_self(self):
        obj = self.factory_cls.build(source="DUMMY SOURCE")

        assert obj.get_stats_summary_changes() == []

    def test_get_stats_summary_changes_return_empty_list_if_boundary_leaf(self):
        obj = self.factory_cls.build(source=SpecieDistribution.DataSource.SELF)

        with patch.object(obj.boundary, "is_leaf", return_value=True):
            assert obj.get_status_changes() == []

    def test_get_stats_summary_changes(self, taxon_root, country_bl, freezer):
        b_root = BoundaryFactory(boundary_layer=country_bl)

        bl_province = BoundaryLayerFactory(parent=country_bl, boundary_type=b_root.boundary_type)
        b_child1 = BoundaryFactory(parent=b_root, boundary_layer=bl_province)
        b_child2 = BoundaryFactory(parent=b_root, boundary_layer=bl_province)
        _ = BoundaryFactory(parent=b_root, boundary_layer=bl_province)
        _ = BoundaryFactory(parent=b_root, boundary_layer=bl_province)

        t_spec_complex = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES_COMPLEX)
        t_spec = TaxonFactory(parent=t_spec_complex, rank=Taxon.TaxonomicRank.SPECIES)

        list_create_species_distribution = [
            (
                datetime.fromisoformat("2022-11-04T00:05:00Z"),
                dict(
                    boundary=b_child1,
                    taxon=t_spec_complex,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.REPORTED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-05T00:05:00Z"),
                dict(
                    boundary=b_child1,
                    taxon=t_spec,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.INTRODUCED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-06T00:05:00Z"),
                dict(
                    boundary=b_child2,
                    taxon=t_spec_complex,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.ESTABLISHED,
                ),
            ),
            (
                datetime.fromisoformat("2022-11-07T00:05:00Z"),
                dict(
                    boundary=b_child2,
                    taxon=t_spec,
                    source=SpecieDistribution.DataSource.SELF,
                    status=SpecieDistribution.DistributionStatus.REPORTED,
                ),
            ),
        ]

        for timestamp, create_kwargs in list_create_species_distribution:
            freezer.move_to(timestamp)
            _obj = self.factory_cls.build(**create_kwargs)
            _obj.save(skip_hooks=True)

        # Getting status changes for taxon complex
        default_result_dict = {
            status_key: {"percentage": 0, "count": 0} for status_key in SpecieDistribution.DistributionStatus.values
        }

        sd_b_root_t_complex = self.factory_cls.build(
            boundary=b_root, taxon=t_spec_complex, source=SpecieDistribution.DataSource.SELF
        )
        assert sd_b_root_t_complex.get_stats_summary_changes() == [
            (
                datetime.fromisoformat("2022-11-04T00:05:00Z"),
                default_result_dict
                | {
                    SpecieDistribution.DistributionStatus.REPORTED: {"count": 1, "percentage": 25},
                    "None": {"count": 3, "percentage": 75},
                },
            ),
            (
                datetime.fromisoformat("2022-11-06T00:05:00Z"),
                default_result_dict
                | {
                    SpecieDistribution.DistributionStatus.REPORTED: {"count": 1, "percentage": 25},
                    SpecieDistribution.DistributionStatus.ESTABLISHED: {"count": 1, "percentage": 25},
                    "None": {"count": 2, "percentage": 50},
                },
            ),
        ]

        assert sd_b_root_t_complex.get_stats_summary_changes(
            from_datetime=datetime.fromisoformat("2022-11-03T00:05:00Z"),
            to_datetime=datetime.fromisoformat("2022-11-05T00:05:00Z"),
        ) == [
            (
                datetime.fromisoformat("2022-11-04T00:05:00Z"),
                default_result_dict
                | {
                    SpecieDistribution.DistributionStatus.REPORTED: {"count": 1, "percentage": 25},
                    "None": {"count": 3, "percentage": 75},
                },
            )
        ]

        # Getting status changes for taxon species
        sd_b_root_t_specie = self.factory_cls.build(
            boundary=b_root, taxon=t_spec, source=SpecieDistribution.DataSource.SELF
        )
        assert sd_b_root_t_specie.get_stats_summary_changes() == [
            (
                datetime.fromisoformat("2022-11-05T00:05:00Z"),
                default_result_dict
                | {
                    SpecieDistribution.DistributionStatus.INTRODUCED: {"count": 1, "percentage": 25},
                    "None": {"count": 3, "percentage": 75},
                },
            ),
            (
                datetime.fromisoformat("2022-11-07T00:05:00Z"),
                default_result_dict
                | {
                    SpecieDistribution.DistributionStatus.INTRODUCED: {"count": 1, "percentage": 25},
                    SpecieDistribution.DistributionStatus.REPORTED: {"count": 1, "percentage": 25},
                    "None": {"count": 2, "percentage": 50},
                },
            ),
        ]

    def test__rebuild_history_raise_ValueError_if_from_date_is_greater_than_any_change(self):
        obj = self.factory_cls.build()

        with pytest.raises(ValueError):
            obj._rebuild_history(
                from_datetime=datetime.fromisoformat("2022-11-07T00:05:00Z"),
                status_changes=[
                    (datetime.fromisoformat("2022-11-05T00:05:00Z"), object()),
                ],
                stats_summary_changes=[],
            )

        with pytest.raises(ValueError):
            obj._rebuild_history(
                from_datetime=datetime.fromisoformat("2022-11-07T00:05:00Z"),
                status_changes=[],
                stats_summary_changes=[
                    (datetime.fromisoformat("2022-11-05T00:05:00Z"), object()),
                ],
            )

    def test__rebuild_history_with_empty_changes_and_from_the_beggining(self, freezer, country_bl, taxon_specie):
        b = BoundaryFactory(boundary_layer=country_bl)
        # Creating new Species Distribution
        freezer.move_to(datetime.fromisoformat("2022-11-05T00:05:00Z"))
        obj = self.factory_cls(
            boundary=b,
            taxon=taxon_specie,
            status=SpecieDistribution.DistributionStatus.REPORTED,
        )

        # Updating
        last_update_datetime = datetime.fromisoformat("2022-11-06T00:05:00Z")
        freezer.move_to(last_update_datetime)
        obj.status = SpecieDistribution.DistributionStatus.INTRODUCED
        obj.save()

        freezer.move_to(datetime.fromisoformat("2022-11-07T00:05:00Z"))

        assert obj.history.count() == 2

        obj._rebuild_history(status_changes=[], stats_summary_changes=[])

        assert obj.history.count() == 1

        history_obj = obj.history.first()
        assert history_obj.history_type == "+"
        assert history_obj.history_date == last_update_datetime
        assert history_obj.stats_summary is None
        assert history_obj.status == SpecieDistribution.DistributionStatus.INTRODUCED

    def test__rebuild_history_with_empty_changes_and_setting_from_datetime(self, freezer, country_bl, taxon_specie):
        b = BoundaryFactory(boundary_layer=country_bl)
        # Creating new Species Distribution
        freezer.move_to(datetime.fromisoformat("2022-11-05T00:05:00Z"))
        obj = self.factory_cls(
            boundary=b,
            taxon=taxon_specie,
            status=SpecieDistribution.DistributionStatus.REPORTED,
        )

        # First update
        freezer.move_to(datetime.fromisoformat("2022-11-06T00:05:00Z"))
        obj.status = SpecieDistribution.DistributionStatus.INTRODUCED
        obj.save()

        # Second update
        freezer.move_to(datetime.fromisoformat("2022-11-07T00:05:00Z"))
        obj.status = SpecieDistribution.DistributionStatus.ESTABLISHED
        obj.save()

        freezer.move_to(datetime.fromisoformat("2022-11-08T00:05:00Z"))

        assert obj.history.count() == 3
        prev_histories = list(obj.history.order_by("history_date").all())

        obj._rebuild_history(
            from_datetime=datetime.fromisoformat("2022-11-06T12:05:00Z"), status_changes=[], stats_summary_changes=[]
        )

        assert obj.history.count() == 2
        assert prev_histories[:2] == list(obj.history.order_by("history_date").all())

    @pytest.mark.parametrize("delete_history_before_start", [True, False])
    def test__rebuild_history(self, freezer, delete_history_before_start):
        freezer.move_to(datetime.fromisoformat("2022-11-05T00:05:00Z"))
        obj = self.factory_cls()

        freezer.move_to(datetime.fromisoformat("2023-01-01T00:05:00Z"))

        if delete_history_before_start:
            obj.history.all().delete()

        obj._rebuild_history(
            status_changes=[
                (datetime.fromisoformat("2022-11-06T00:05:00Z"), SpecieDistribution.DistributionStatus.REPORTED),
                (datetime.fromisoformat("2022-11-09T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
            ],
            stats_summary_changes=[
                (datetime.fromisoformat("2022-11-07T00:05:00Z"), {"dummy_key": "value_1"}),
                (datetime.fromisoformat("2022-11-08T00:05:00Z"), {"dummy_key": "value_2"}),
            ],
        )

        assert obj.history.count() == 4

        first_hist = obj.history.order_by("history_date")[0]
        assert first_hist.history_date == datetime.fromisoformat("2022-11-06T00:05:00Z")
        assert first_hist.history_type == "+"
        assert first_hist.status == SpecieDistribution.DistributionStatus.REPORTED
        assert first_hist.stats_summary is None

        second_hist = obj.history.order_by("history_date")[1]
        assert second_hist.history_date == datetime.fromisoformat("2022-11-07T00:05:00Z")
        assert second_hist.history_type == "~"
        assert second_hist.status == SpecieDistribution.DistributionStatus.REPORTED
        assert second_hist.stats_summary == {"dummy_key": "value_1"}

        third_hist = obj.history.order_by("history_date")[2]
        assert third_hist.history_date == datetime.fromisoformat("2022-11-08T00:05:00Z")
        assert third_hist.history_type == "~"
        assert third_hist.status == SpecieDistribution.DistributionStatus.REPORTED
        assert third_hist.stats_summary == {"dummy_key": "value_2"}

        fourth_hist = obj.history.order_by("history_date")[3]
        assert fourth_hist.history_date == datetime.fromisoformat("2022-11-09T00:05:00Z")
        assert fourth_hist.history_type == "~"
        assert fourth_hist.status == SpecieDistribution.DistributionStatus.INTRODUCED
        assert fourth_hist.stats_summary == {"dummy_key": "value_2"}

    def test_update_has_hook_before_create(self):
        obj = self.factory_cls.build()

        assert hook(hook=BEFORE_CREATE) in obj.update._hooked

    def test_update_calls__rebuild_history_if_object_already_created(self, taxon_specie):
        obj = self.factory_cls()

        with patch.object(obj, "_rebuild_history") as mocked_method:
            with patch.object(obj, "get_status_changes", return_value=[]):
                with patch.object(obj, "get_stats_summary_changes", return_value=[]):
                    obj.update(from_datetime="DUMMY DATETIME")

                    mocked_method.assert_called_once_with(
                        status_changes=[], stats_summary_changes=[], from_datetime="DUMMY DATETIME"
                    )

    def test_update_calls_save__with_skipped_history_creation_if_object_already_created(self):
        obj = self.factory_cls()

        with patch.object(obj, "save"):
            obj.update()

            assert obj.skip_history_when_saving is True

    @pytest.mark.parametrize("set_None", [True, False])
    def test_update_sets_last_changes_to_current_values_or_None(self, set_None, freezer):
        freezer.move_to(datetime.fromisoformat("2023-01-01T00:05:00Z"))
        obj = self.factory_cls.build()

        get_status_changes_return = [
            (datetime.fromisoformat("2022-11-06T00:05:00Z"), SpecieDistribution.DistributionStatus.REPORTED),
            (datetime.fromisoformat("2022-11-09T00:05:00Z"), SpecieDistribution.DistributionStatus.INTRODUCED),
        ]

        get_stats_summary_changes_return = [
            (datetime.fromisoformat("2022-11-07T00:05:00Z"), {"dummy_key": "value_1"}),
            (datetime.fromisoformat("2022-11-08T00:05:00Z"), {"dummy_key": "value_2"}),
        ]

        with patch.object(obj, "get_status_changes", return_value=get_status_changes_return if not set_None else []):
            with patch.object(
                obj, "get_stats_summary_changes", return_value=get_stats_summary_changes_return if not set_None else []
            ):
                obj.update()

                assert obj.status == (SpecieDistribution.DistributionStatus.INTRODUCED if not set_None else None)
                assert obj.status_since == (
                    datetime.fromisoformat("2022-11-09T00:05:00Z")
                    if not set_None
                    else datetime.fromisoformat("2023-01-01T00:05:00Z")
                )
                assert obj.stats_summary == ({"dummy_key": "value_2"} if not set_None else None)

    def test_update_parents_is_called_after_create(self):
        obj = self.factory_cls.build()

        assert hook(hook=AFTER_CREATE) in obj.update_parents._hooked

    def test_update_parents_is_called_after__update_status(self):
        obj = self.factory_cls.build()

        assert hook(hook=AFTER_UPDATE, when="status", has_changed=True) in obj.update_parents._hooked

    def test_update_parents_does_nothing_if_not_source_self(self):
        obj = self.factory_cls()
        obj.source = "DUMMY SOURCE"

        assert obj.update_parents() is None

    def test_update_parents_calls__update_on_all_parents(self, taxon_specie):
        p_boundary = BoundaryFactory(name="country")
        c_boundary = BoundaryFactory(name="city", parent=p_boundary, boundary_layer=p_boundary.boundary_layer)

        c_species_obj = self.factory_cls.build(
            status=SpecieDistribution.DistributionStatus.REPORTED,
            boundary=c_boundary,
            taxon=taxon_specie,
            source=SpecieDistribution.DataSource.SELF,
        )
        c_species_obj.save(skip_hooks=True)

        # Crete one parent object to test it calls update
        # same taxon, parent boundary
        p_taxon_obj = self.factory_cls.build(
            boundary=p_boundary, taxon=c_species_obj.taxon, source=c_species_obj.source
        )
        p_taxon_obj.save(skip_hooks=True)

        # Assert that the current object has called update
        with patch.object(self.model, "objects", MockSet(c_species_obj, p_taxon_obj, model=self.model)):
            with patch.object(p_taxon_obj, "update", return_value=None) as mocked_update:
                # Call update parents
                c_species_obj.update_parents()

            mocked_update.assert_called_once_with()

    def test_update_parents(self):
        taxon_genus = TaxonFactory(rank=Taxon.TaxonomicRank.GENUS)
        taxon_complex = TaxonFactory(rank=Taxon.TaxonomicRank.SPECIES_COMPLEX, parent=taxon_genus)
        taxon_specie = TaxonFactory(rank=Taxon.TaxonomicRank.SPECIES, parent=taxon_complex)

        p_boundary = BoundaryFactory(name="country")
        c_boundary = BoundaryFactory(name="province", parent=p_boundary, boundary_layer=p_boundary.boundary_layer)
        l_boundary = BoundaryFactory(
            name="city", with_geometry=True, parent=c_boundary, boundary_layer=c_boundary.boundary_layer
        )

        point = l_boundary.geometry.point_on_surface

        # First taxon complex report
        _ = IndividualReportFactory(
            published=True,
            observed_at=datetime.fromisoformat("2022-11-04T00:05:00Z"),
            location__point=point,
            individuals=[IndividualFactory(taxon=taxon_specie)],
        )

        # Cretae leafs objects
        l_species_obj = self.factory_cls.build(
            status=SpecieDistribution.DistributionStatus.REPORTED,
            boundary=l_boundary,
            taxon=taxon_specie,
            source=SpecieDistribution.DataSource.SELF,
        )
        l_species_obj.save(skip_hooks=True)

        # Call update parents
        l_species_obj.update_parents()

        # Assert parent boundaries
        l_complex_obj = self.model.objects.get(
            boundary=l_boundary, taxon=taxon_complex, source=SpecieDistribution.DataSource.SELF
        )
        assert l_complex_obj.status == SpecieDistribution.DistributionStatus.REPORTED

        c_species_obj = self.model.objects.get(
            boundary=c_boundary, taxon=taxon_specie, source=SpecieDistribution.DataSource.SELF
        )
        assert c_species_obj.status == SpecieDistribution.DistributionStatus.REPORTED

        c_complex_obj = self.model.objects.get(
            boundary=c_boundary, taxon=taxon_complex, source=SpecieDistribution.DataSource.SELF
        )
        assert c_complex_obj.status == SpecieDistribution.DistributionStatus.REPORTED

        p_species_obj = self.model.objects.get(
            boundary=p_boundary, taxon=taxon_specie, source=SpecieDistribution.DataSource.SELF
        )
        assert p_species_obj.status == SpecieDistribution.DistributionStatus.REPORTED

        p_complex_obj = self.model.objects.get(
            boundary=p_boundary, taxon=taxon_complex, source=SpecieDistribution.DataSource.SELF
        )
        assert p_complex_obj.status == SpecieDistribution.DistributionStatus.REPORTED

        # assert non species was not created
        assert not self.model.objects.filter(taxon=taxon_genus).exists()

        assert self.model.objects.count() == 6  # 1 init + 5 created

    def test_status_since_is_set_to_now_on_status_change(self, freezer, taxon_specie):
        freezer.move_to(datetime.fromisoformat("2022-11-07T00:05:00Z"))
        obj = self.factory_cls.build(boundary=BoundaryFactory(), taxon=taxon_specie, status=None)
        obj.save()
        assert obj.status_since == datetime.fromisoformat("2022-11-07T00:05:00Z")

        freezer.move_to(datetime.fromisoformat("2022-11-08T00:05:00Z"))
        obj.status = SpecieDistribution.DistributionStatus.INTRODUCED
        obj.save()
        assert obj.status_since == datetime.fromisoformat("2022-11-08T00:05:00Z")

        freezer.move_to(datetime.fromisoformat("2022-11-10T00:05:00Z"))
        obj.status = SpecieDistribution.DistributionStatus.ESTABLISHED
        obj.status_since = datetime.fromisoformat("2022-11-09T00:05:00Z")
        obj.save()

        assert obj.status_since == datetime.fromisoformat("2022-11-09T00:05:00Z")

    # Methods - check made on save
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

    def test_post_save_calls__rebuild_history(self, taxon_specie):
        obj = self.factory_cls.build(boundary=BoundaryFactory(), taxon=taxon_specie)

        with patch.object(obj, "_rebuild_history") as mocked_method:
            obj.save()
            mocked_method.assert_called_once()

        # Second save does not call rebuild anymore.
        with patch.object(obj, "_rebuild_history") as mocked_method:
            obj.save()
            mocked_method.assert_not_called()

    def test_history_record_is_created_on_creation(self):
        assert self.model.objects.all().count() == 0
        assert self.model.history.all().count() == 0

        _ = self.factory_cls()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        assert self.model.history.first().history_type == "+"

    @pytest.mark.parametrize(
        "fields_changed, history_created",
        [
            (("status",), True),
            (("stats_summary",), True),
            (("status", "stats_summary"), True),
            (("boundary"), False),
            ((), False),
        ],
    )
    def test_history_record_is_create_on_field_change(self, fields_changed, history_created):
        obj = self.factory_cls()

        with patch.object(obj, "has_changed", side_effect=lambda field_name: field_name in fields_changed):
            obj.save()

            assert self.model.history.all().count() == 2 if history_created else 1

    def test_historical_records_are_deleted_on_master_deletion(self):
        obj = self.factory_cls()

        assert self.model.objects.all().count() == 1
        assert self.model.history.all().count() == 1

        obj.delete()

        assert self.model.objects.all().count() == 0
        assert self.model.history.all().count() == 0

    # meta
    def test_unique_contraint_boundary_taxon_source(self):
        sd = self.factory_cls()

        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = self.factory_cls(boundary=sd.boundary, taxon=sd.taxon, source=sd.source)

    def test_status_since_can_not_be_future_date(self):
        obj = self.factory_cls()
        with pytest.raises(IntegrityError, match=r"violates check constraint"):
            obj.status_since = timezone.now() + timedelta(seconds=10)
            obj.save()
