from django.urls import reverse

from mosquito_alert.breeding_sites.models import BreedingSite
from mosquito_alert.geo.tests.factories import LocationFactory

from .factories import BreedingSiteFactory


class TestBreedingSiteAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:breeding_sites_breedingsite_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_add(self, admin_client):
        url = reverse("admin:breeding_sites_breedingsite_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "type": BreedingSite.BreedingSiteTypes.STORM_DRAIN.value,
                "location": LocationFactory().pk,
            },
        )
        assert response.status_code == 302
        assert BreedingSite.objects.filter(
            type=BreedingSite.BreedingSiteTypes.STORM_DRAIN.value,
        ).exists()

    def test_view(self, admin_client):
        breeding_site = BreedingSiteFactory()
        url = reverse(
            "admin:breeding_sites_breedingsite_change",
            kwargs={"object_id": breeding_site.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
