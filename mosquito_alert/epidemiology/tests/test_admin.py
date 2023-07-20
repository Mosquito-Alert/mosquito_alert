from django.urls import reverse
from pytest_django.asserts import assertContains

from mosquito_alert.taxa.tests.factories import SpecieDistributionFactory

from ..models import Disease, DiseaseVector
from .factories import DiseaseFactory, DiseaseVectorFactory


class TestDiseasesAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:epidemiology_disease_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_add(self, admin_client):
        url = reverse("admin:epidemiology_disease_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "name_en": "test disease",
                "DiseaseVector_diseases-TOTAL_FORMS": "0",
                "DiseaseVector_diseases-INITIAL_FORMS": "0",
            },
        )
        assert response.status_code == 302
        assert Disease.objects.filter(name="test disease").exists()

    def test_view(self, admin_client):
        disease = DiseaseFactory()
        url = reverse("admin:epidemiology_disease_change", kwargs={"object_id": disease.pk})
        response = admin_client.get(url)
        assert response.status_code == 200


class TestDiseaseVectorsAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:epidemiology_diseasevector_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client, taxon_specie):
        taxon_specie.name = "Test taxon"
        taxon_specie.save()

        taxon_vector = DiseaseVectorFactory(taxon=taxon_specie)

        url = reverse("admin:epidemiology_diseasevector_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200
        assertContains(response=response, text=f'value="{taxon_vector.id}"')

    def test_taxon_filter(self, admin_client):
        url = reverse("admin:epidemiology_diseasevector_changelist")
        response = admin_client.get(url, data={"taxon__exact": "1"})
        assert response.status_code == 200

    def test_diseases_filter(self, admin_client):
        url = reverse("admin:epidemiology_diseasevector_changelist")
        response = admin_client.get(url, data={"diseases__exact": "1"})
        assert response.status_code == 200

    def test_add(self, admin_client, taxon_specie):
        url = reverse("admin:epidemiology_diseasevector_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        disease = DiseaseFactory()

        response = admin_client.post(
            url,
            data={
                "taxon": f"{taxon_specie.pk}",
                "diseases": f"{disease.pk}",
            },
        )
        assert response.status_code == 302
        assert DiseaseVector.objects.filter(taxon=taxon_specie).exists()

    def test_view(self, admin_client):
        disease_vector = DiseaseVectorFactory()
        url = reverse(
            "admin:epidemiology_diseasevector_change",
            kwargs={"object_id": disease_vector.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200


class TestDiseaseVectorDistributionAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:epidemiology_diseasevectordistribution_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_search(self, admin_client):
        url = reverse("admin:epidemiology_diseasevectordistribution_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == 200

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:epidemiology_diseasevectordistribution_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client, taxon_specie):
        taxon_vector = DiseaseVectorFactory(taxon=taxon_specie)

        distribution = SpecieDistributionFactory(taxon=taxon_vector.taxon)

        url = reverse(
            "admin:epidemiology_diseasevectordistribution_change",
            kwargs={"object_id": distribution.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_history(self, admin_client, taxon_specie):
        taxon_vector = DiseaseVectorFactory(taxon=taxon_specie)

        distribution = SpecieDistributionFactory(taxon=taxon_vector.taxon)

        url = reverse(
            "admin:epidemiology_diseasevectordistribution_history",
            kwargs={"object_id": distribution.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
