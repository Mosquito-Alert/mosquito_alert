import pytest
from django.urls import reverse

from ..admin import BiteReportChildAdmin, BreedingSiteReportChildAdmin, IndividualReportAdmin, ReportParentAdmin
from ..models import BiteReport, BreedingSiteReport, IndividualReport
from .factories import BiteReportFactory, BreedingSiteReportFactory, IndividualReportFactory


class BaseRecoverableReportMixin:
    def test_recoverlist(self, admin_client):
        url = reverse(f"admin:{self.prefix}_recoverlist")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestReportParentAdmin(BaseRecoverableReportMixin):
    prefix = "reports_report"

    def test_changelist(self, admin_client):
        url = reverse(f"admin:{self.prefix}_changelist")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize("fieldname", ["observed_at", "created_at"])
    def test_filters(self, fieldname):
        assert fieldname in ReportParentAdmin.list_filter

    def test_add(self, admin_client):
        url = reverse(f"admin:{self.prefix}_add")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "factory_cls",
        [IndividualReportFactory, BiteReportFactory, BreedingSiteReportFactory],
    )
    def test_child_view(self, admin_client, factory_cls):
        report = factory_cls()
        url = reverse(
            f"admin:{self.prefix}_change",  # noqa: E231
            kwargs={"object_id": report.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200


class BaseReportChildAdmin(BaseRecoverableReportMixin):
    # NOTE: Override these when inherit.
    admin_cls = None
    prefix = None

    @pytest.fixture
    def factory_cls(self):
        return None

    common_payload = {
        "observed_at_0": "2023-07-14",
        "observed_at_1": "00:00:00",
        "notes": "",
        "location_point": '{"type": "Point", "coordinates": [557144.124692098470405, 5943107.339493401348591],}',
        "Report_photos-TOTAL_FORMS": "0",
        "Report_photos-INITIAL_FORMS": "0",
        "moderation-flag-content_type-object_id-TOTAL_FORMS": "0",
        "moderation-flag-content_type-object_id-INITIAL_FORMS": "0",
        "moderation-flag-content_type-object_id-empty-flags-TOTAL_FORMS": "0",
        "moderation-flag-content_type-object_id-empty-flags-INITIAL_FORMS": "0",
    }

    def test_changelist(self, admin_client):
        url = reverse(f"admin:{self.prefix}_changelist")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

    @pytest.mark.parametrize("fieldname", ["observed_at", "created_at"])
    def test_filters(self, fieldname):
        assert fieldname in self.admin_cls.list_filter

    def test_child_view(self, admin_client, factory_cls):
        report = factory_cls()
        url = reverse(
            f"admin:{self.prefix}_change",  # noqa: E231
            kwargs={"object_id": report.pk},
        )
        response = admin_client.get(url)
        assert response.status_code == 200


class TestBiteReportChildAdmin(BaseReportChildAdmin):
    admin_cls = BiteReportChildAdmin
    prefix = "reports_bitereport"

    @pytest.fixture
    def factory_cls(self):
        return BiteReportFactory

    def test_add(self, admin_client):
        url = reverse(f"admin:{self.prefix}_add")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

        assert BiteReport.objects.all().count() == 0

        response = admin_client.post(
            url,
            data=self.common_payload
            | {
                "BiteReport_bites-TOTAL_FORMS": "0",
                "BiteReport_bites-INITIAL_FORMS": "0",
            },
        )

        assert response.status_code == 302
        assert BiteReport.objects.all().count() == 1


class TestBreedingSiteReportChildAdmin(BaseReportChildAdmin):
    admin_cls = BreedingSiteReportChildAdmin
    prefix = "reports_breedingsitereport"

    @pytest.fixture
    def factory_cls(self):
        return BreedingSiteReportFactory

    def test_add(self, admin_client):
        url = reverse(f"admin:{self.prefix}_add")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

        assert BreedingSiteReport.objects.all().count() == 0

        response = admin_client.post(
            url,
            data=self.common_payload
            | {
                "breeding_site": "",
                "has_water": "on",
            },
        )

        assert response.status_code == 302
        assert BreedingSiteReport.objects.all().count() == 1


class TestIndividualReportAdmin(BaseReportChildAdmin):
    admin_cls = IndividualReportAdmin
    prefix = "reports_individualreport"

    @pytest.fixture
    def factory_cls(self):
        return IndividualReportFactory

    def test_add(self, admin_client):
        url = reverse(f"admin:{self.prefix}_add")  # noqa: E231
        response = admin_client.get(url)
        assert response.status_code == 200

        assert IndividualReport.objects.all().count() == 0

        response = admin_client.post(
            url,
            data=self.common_payload
            | {
                "taxon": "",
                "IndividualReport_individuals-TOTAL_FORMS": 0,
                "IndividualReport_individuals-INITIAL_FORMS": 0,
            },
        )

        assert response.status_code == 302
        assert IndividualReport.objects.all().count() == 1
