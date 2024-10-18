from django.urls import reverse

from mosquito_alert.geo.tests.factories import BoundaryFactory
from mosquito_alert.users.tests.factories import UserFactory

from ..models import BoundaryAuthorization, BoundaryMembership
from .factories import BoundaryAuthorizationFactory


class TestBoundaryAuthorizationAdmin:
    def test_changelist(self, admin_client):
        url = reverse("admin:authorization_boundaryauthorization_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_add(self, admin_client, freezer):
        url = reverse("admin:authorization_boundaryauthorization_add")
        response = admin_client.get(url)
        assert response.status_code == 200

        boundary = BoundaryFactory()
        user = UserFactory()

        response = admin_client.post(
            url,
            data={
                "boundary": boundary.pk,
                "supervisor_exclusivity_days": "15",
                "memberships-TOTAL_FORMS": "1",
                "memberships-INITIAL_FORMS": "0",
                "memberships-0-user": user.pk,
                "memberships-0-role": BoundaryMembership.RoleType.SUPERVISOR.value,
            },
        )
        assert response.status_code == 302
        assert BoundaryAuthorization.objects.filter(boundary=boundary).exists()

    def test_view(self, admin_client):
        boundary_auth = BoundaryAuthorizationFactory()
        url = reverse("admin:authorization_boundaryauthorization_change", kwargs={"object_id": boundary_auth.pk})
        response = admin_client.get(url)
        assert response.status_code == 200
