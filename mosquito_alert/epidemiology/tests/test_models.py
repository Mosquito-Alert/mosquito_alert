import pytest
from django.db.utils import DataError, IntegrityError

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import SpecieDistributionFactory, TaxonFactory

from ..models import Disease, DiseaseVector, DiseaseVectorDistribution
from .factories import DiseaseFactory, DiseaseVectorFactory


@pytest.mark.django_db
class TestDiseaseModel:
    def test_default_order_by_name(self):
        d1 = DiseaseFactory(name="Z")
        d2 = DiseaseFactory(name="A")

        assert frozenset(Disease.objects.all()) == frozenset([d2, d1])

    def test_name_must_be_unique(self):
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = DiseaseFactory.create_batch(size=2, name="Unique Name")

    @pytest.mark.parametrize(
        "name, output_raises",
        [
            ("a" * 63, False),
            ("a" * 64, False),
            ("a" * 65, True),
        ],
    )
    def test_name_max_length_is_64(self, name, output_raises):
        if output_raises:
            with pytest.raises(DataError):
                DiseaseFactory(name=name)
        else:
            DiseaseFactory(name=name)

    def test__str__(self):
        disease = DiseaseFactory(name="Malaria")
        assert disease.__str__() == "Malaria"


@pytest.mark.django_db
class TestDiseaseVectorModel:
    def test_diseasse_vector_one2one_taxon(self, taxon_specie):
        with pytest.raises(IntegrityError, match=r"unique constraint"):
            _ = DiseaseVectorFactory.create_batch(size=2, taxon=taxon_specie)

    def test_disease_vector_pk_is_taxon(self, taxon_specie):
        dv = DiseaseVectorFactory(taxon=taxon_specie)

        assert dv.pk == taxon_specie.pk

    def test_cascade_taxon_deletion(self):
        dv = DiseaseVectorFactory()
        dv.taxon.delete()

        assert DiseaseVector.objects.all().count() == 0

    def test_taxon_can_not_be_null(self):
        with pytest.raises(IntegrityError, match=r"not-null constraint"):
            DiseaseVectorFactory(taxon=None)

    def test_taxon_related_name(self, taxon_specie):
        dv = DiseaseVectorFactory(taxon=taxon_specie)

        assert taxon_specie.disease_vector == dv

    def test_taxon_should_be_species_rank(self):
        with pytest.raises(ValueError, match=r"Taxon must be species rank."):
            DiseaseVectorFactory(taxon__rank=Taxon.TaxonomicRank.DOMAIN)

    def test_default_ordering_is_taxon_name(self, taxon_root):
        dv1 = DiseaseVectorFactory(taxon__name="z", taxon__parent=taxon_root)
        dv2 = DiseaseVectorFactory(taxon__name="a", taxon__parent=taxon_root)

        assert list(DiseaseVector.objects.all()) == [dv2, dv1]

    def test_diseases_related_name(self):
        disease = DiseaseFactory()
        dv = DiseaseVectorFactory(diseases=[disease])

        assert list(disease.disease_vectors.all()) == [dv]

    def test__str__(self):
        dv = DiseaseVectorFactory(taxon__name="Random name")

        assert dv.__str__() == "Random name"


@pytest.mark.django_db
class TestDiseaseVectorDistribution:
    def test_should_filter_by_taxon_vectors(self, taxon_root, country_bl):
        taxon_not_vector = TaxonFactory(parent=taxon_root, rank=Taxon.TaxonomicRank.SPECIES)
        disease_vector = DiseaseVectorFactory(taxon__parent=taxon_root, taxon__name="test")

        _ = SpecieDistributionFactory(taxon=taxon_not_vector, boundary__boundary_layer=country_bl)
        _ = SpecieDistributionFactory(taxon=disease_vector.taxon, boundary__boundary_layer=country_bl)

        assert list(DiseaseVectorDistribution.objects.values_list("taxon", flat=True).all()) == [
            disease_vector.taxon.pk
        ]
