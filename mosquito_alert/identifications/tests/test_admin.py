from django.urls import reverse

from ..models import IdentifierUserProfile
from .factories import IdentifierUserProfileFactory


class TestIdentifierUserProfileAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:identifications_identifieruserprofile_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_is_superexpert_filter(self, admin_client):
        url = reverse("admin:identifications_identifieruserprofile_changelist")
        response = admin_client.get(url, data={"is_superexpert__exact": "1"})
        assert response.status_code == 200

        response = admin_client.get(url, data={"is_superexpert__exact": "0"})
        assert response.status_code == 200

    def test_add(self, admin_client, user):
        url = reverse("admin:identifications_identifieruserprofile_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        response = admin_client.post(
            url,
            data={"user": user.pk, "is_superexpert": "1"},
        )
        assert response.status_code == 302
        instance = IdentifierUserProfile.objects.get(user=user)

        assert instance.pk == user.pk
        assert instance.is_superexpert is True

    def test_view(self, admin_client):
        bite = IdentifierUserProfileFactory()
        url = reverse(
            "admin:identifications_identifieruserprofile_change",
            kwargs={"object_id": bite.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
