from datetime import timedelta

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.utils import timezone

from mosquito_alert.images.tests.factories import PhotoFactory

from ..admin import IndividualAdmin
from ..models import Individual
from .factories import IndividualFactory


@pytest.mark.django_db
class TestIndividualAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:individuals_individual_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_taxon_filter(self, admin_client, taxon_specie):
        url = reverse("admin:individuals_individual_changelist")
        response = admin_client.get(url, data={"taxon__id__exact": taxon_specie.pk})
        assert response.status_code == 200

    def test_is_identified_filter(self, admin_client):
        url = reverse("admin:individuals_individual_changelist")
        response = admin_client.get(url, data={"is_identified__exact": "1"})
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "fieldname",
        [
            "taxon",
            "is_identified",
            "show_result_prob_tree",
            "show_community_prob_tree",
            "show_computervision_prob_tree",
        ],
    )
    def test_readonly_fields(self, fieldname):
        assert fieldname in IndividualAdmin.readonly_fields

    def test_add(self, admin_client):
        url = reverse("admin:individuals_individual_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        assert Individual.objects.all().count() == 0

        response = admin_client.post(
            url,
            data={
                "Individual_photos-TOTAL_FORMS": "0",
                "Individual_photos-INITIAL_FORMS": "0",
                "useridentificationsuggestion_set-TOTAL_FORMS": "0",
                "useridentificationsuggestion_set-INITIAL_FORMS": "0",
            },
        )

        assert response.status_code == 302
        assert Individual.objects.all().count() == 1

    def test_preview_thumbnail_is_the_newest_image_html(self):
        t = timezone.now()
        old = PhotoFactory(created_at=t)
        oldest = PhotoFactory(created_at=t - timedelta(seconds=10))
        newest = PhotoFactory(created_at=t + timedelta(seconds=10))

        i = IndividualFactory(photos=[old, newest, oldest])

        individual_admin = IndividualAdmin(model=Individual, admin_site=AdminSite())

        assert (
            individual_admin.thumbnail(i)
            == f"<img src='{newest.image.url}' height='75' />"
        )

    def test_view(self, admin_client):
        i = IndividualFactory()
        url = reverse(
            "admin:individuals_individual_change",
            kwargs={"object_id": i.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200
