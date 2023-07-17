import pytest
from django.db.models.deletion import ProtectedError

from mosquito_alert.taxa.models import Taxon
from mosquito_alert.taxa.tests.factories import TaxonFactory

from .factories import IndividualFactory


@pytest.mark.django_db
class TestIndividual:
    def test_taxon_can_be_nullable(self):
        IndividualFactory(taxon=None)

    def test_raise_if_taxon_is_deleted(self, taxon_specie):
        _ = IndividualFactory(taxon=taxon_specie)
        with pytest.raises(ProtectedError):
            taxon_specie.delete()

    def test_is_not_identified_by_default(self):
        assert not IndividualFactory().is_identified

    def test_is_identified_become_true_on_taxon_change_is_specie(self, taxon_specie):
        i = IndividualFactory(taxon=None)

        assert not i.is_identified

        i.taxon = taxon_specie
        i.save()

        assert i.is_identified

    def test_is_identified_become_false_on_taxon_change_is_not_specie(
        self, taxon_specie, taxon_root
    ):
        i = IndividualFactory(taxon=taxon_specie)

        assert i.is_identified

        new_taxon = TaxonFactory(rank=Taxon.TaxonomicRank.GENUS, parent=taxon_root)
        i.taxon = new_taxon
        i.save()

        assert not i.is_identified

    def test__str__(self, taxon_specie):
        i = IndividualFactory(taxon=taxon_specie)

        assert i.__str__() == taxon_specie.__str__()

        i.taxon = None
        i.save()

        assert i.__str__() == f"Not-identified individual (id={i.pk})"
