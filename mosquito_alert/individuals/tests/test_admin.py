import pytest
from django.urls import reverse

from ..admin import IndividualAdmin
from .factories import IndividualFactory


@pytest.mark.django_db
class TestIndividualAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:individuals_individual_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "fieldname",
        [
            "taxon",
            "is_identified",
        ],
    )
    def test_readonly_fields(self, fieldname):
        assert fieldname in IndividualAdmin.readonly_fields

    def test_add_is_not_allowed(self, admin_client):
        url = reverse("admin:individuals_individual_add")
        response = admin_client.get(url)
        assert response.status_code == 403

    def test_view(self, admin_client):
        i = IndividualFactory()
        url = reverse(
            "admin:individuals_individual_change",
            kwargs={"object_id": i.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
