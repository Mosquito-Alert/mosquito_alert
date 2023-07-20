from django.urls import reverse
from django.utils import timezone

from mosquito_alert.bites.models import Bite

from .factories import BiteFactory


class TestBiteAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:bites_bite_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_add(self, admin_client, freezer):
        url = reverse("admin:bites_bite_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={
                "body_part": Bite.BodyParts.HEAD.value,
            },
        )
        assert response.status_code == 302
        assert Bite.objects.filter(body_part=Bite.BodyParts.HEAD.value, datetime=timezone.now()).exists()

    def test_view(self, admin_client):
        bite = BiteFactory()
        url = reverse("admin:bites_bite_change", kwargs={"object_id": bite.pk})
        response = admin_client.get(url)
        assert response.status_code == 200
