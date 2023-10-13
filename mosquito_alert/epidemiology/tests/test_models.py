import pytest
from django.db import models

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import SpecieDistributionFactory, TaxonFactory
from mosquito_alert.utils.tests.test_models import AbstractDjangoModelTestMixin

from ..models import Disease, DiseaseVector, DiseaseVectorDistribution
from .factories import DiseaseFactory, DiseaseVectorFactory


@pytest.mark.django_db
class TestDiseaseModel(AbstractDjangoModelTestMixin):
    model = Disease
    factory_cls = DiseaseFactory

    # fields
    def test_name_is_unique(self):
        assert self.model._meta.get_field("name").unique

    def test_name_max_length_is_64(self):
        assert self.model._meta.get_field("name").max_length == 64

    # meta
    def test_ordering_ascending_name(self):
        assert self.model._meta.ordering == ["name"]

    def test__str__(self):
        disease = DiseaseFactory(name="Malaria")
        assert disease.__str__() == "Malaria"


@pytest.mark.django_db
class TestDiseaseVectorModel(AbstractDjangoModelTestMixin):
    model = DiseaseVector
    factory_cls = DiseaseVectorFactory

    # fields
    def test_taxon_fk_is_unique(self):
        assert self.model._meta.get_field("taxon").unique

    def test_taxon_is_pk(self):
        assert self.model._meta.get_field("taxon").primary_key

    def test_taxon_deletion_is_cascaded(self):
        _on_delete = self.model._meta.get_field("taxon").remote_field.on_delete
        assert _on_delete == models.CASCADE

    def test_taxon_related_name(self):
        assert self.model._meta.get_field("taxon").remote_field.related_name == "disease_vector"

    def test_taxon_can_not_be_null(self):
        assert not self.model._meta.get_field("taxon").null

    def test_diseases_related_name(self):
        assert self.model._meta.get_field("diseases").remote_field.related_name == "disease_vectors"

    # methods
    def test_taxon_should_be_species_rank(self):
        with pytest.raises(ValueError, match=r"Taxon must be species rank."):
            DiseaseVectorFactory(taxon__rank=Taxon.TaxonomicRank.CLASS)

    # meta
    def test_default_ordering_is_taxon_name_asc(self, taxon_root):
        assert self.model._meta.ordering == ["taxon__name"]

    def test__str__(self):
        dv = DiseaseVectorFactory(taxon__name="Random name")

        assert dv.__str__() == "Random name"


@pytest.mark.django_db
class TestDiseaseVectorDistribution(AbstractDjangoModelTestMixin):
    model = DiseaseVectorDistribution
    factory_cls = None

    def test_should_filter_by_taxon_vectors(self, taxon_root, country_bl):
        taxon_not_vector = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)
        disease_vector = DiseaseVectorFactory(taxon__parent=taxon_root, taxon__name="test")

        _ = SpecieDistributionFactory(taxon=taxon_not_vector, boundary__boundary_layer=country_bl)
        _ = SpecieDistributionFactory(taxon=disease_vector.taxon, boundary__boundary_layer=country_bl)

        assert list(DiseaseVectorDistribution.objects.values_list("taxon", flat=True).all()) == [
            disease_vector.taxon.pk
        ]
