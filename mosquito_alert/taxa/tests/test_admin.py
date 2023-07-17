from django.urls import reverse

from ..admin import TaxonAdmin
from ..models import Taxon


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
