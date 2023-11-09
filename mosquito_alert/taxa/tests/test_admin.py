from django.urls import reverse

from mosquito_alert.geo.tests.factories import BoundaryFactory

from ..admin import TaxonAdmin
from ..models import SpecieDistribution, Taxon
from .factories import SpecieDistributionFactory


class TestTaxonAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:taxa_taxon_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search_by_name(self):
        assert "name" in TaxonAdmin.search_fields

    def test_filter_by_rank(self):
        assert "rank" in TaxonAdmin.list_filter

    def test_add(self, admin_client, taxon_root):
        url = reverse("admin:taxa_taxon_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        assert not Taxon.objects.filter(
            name="Diptera",
        ).exists()

        response = admin_client.post(
            url,
            data={
                "rank": Taxon.TaxonomicRank.KINGDOM.value,
                "name": "Diptera",
                "_position": "sorted-child",
                "_ref_node_id": taxon_root.pk,
            },
        )
        assert response.status_code == 302
        assert Taxon.objects.filter(
            name="Diptera",
        ).exists()

    def test_view(self, admin_client, taxon_specie):
        url = reverse(
            "admin:taxa_taxon_change",
            kwargs={"object_id": taxon_specie.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200


class TestSpecieDistributionAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:taxa_speciedistribution_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client):
        url = reverse("admin:taxa_speciedistribution_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200

    def test_add(self, admin_client, taxon_specie):
        url = reverse("admin:taxa_speciedistribution_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        assert SpecieDistribution.objects.all().count() == 0

        boundary = BoundaryFactory()

        data_source = SpecieDistribution.DataSource.SELF

        response = admin_client.post(
            url,
            data={
                "boundary": f"{boundary.pk}",
                "taxon": f"{taxon_specie.pk}",
                "source": {data_source.value},
                "status": {SpecieDistribution.DistributionStatus.ABSENT.value},
            },
        )
        assert response.status_code == 302
        assert SpecieDistribution.objects.filter(boundary=boundary.pk, taxon=taxon_specie, source=data_source).exists()

    def test_view(self, admin_client, taxon_specie):
        distribution = SpecieDistributionFactory(taxon=taxon_specie)

        url = reverse(
            "admin:taxa_speciedistribution_change",
            kwargs={"object_id": distribution.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_history(self, admin_client, taxon_specie):
        distribution = SpecieDistributionFactory(taxon=taxon_specie)

        url = reverse(
            "admin:taxa_speciedistribution_history",
            kwargs={"object_id": distribution.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
