import pytest
from django.contrib.gis.geos import MultiPolygon, Polygon

from mosquito_alert.geo.tests.factories import NutsEuropeFactory
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership
from mosquito_alert.workspaces.tests.factories import (
    WorkspaceCollaborationGroupFactory,
    WorkspaceFactory,
)


@pytest.fixture
def country_workspace(es_country):
    workspace = Workspace.objects.filter(country=es_country, geom__isnull=True).first()
    return workspace or WorkspaceFactory(country=es_country)


@pytest.mark.django_db
class TestCanViewReportStatsForArea:
    @pytest.mark.parametrize("role", WorkspaceMembership.Role.values)
    def test_country_workspace_members_can_view_country_and_subregion(
        self, user, es_country, country_workspace, role
    ):
        WorkspaceMembership.objects.create(
            user=user, workspace=country_workspace, role=role
        )
        subregion = NutsEuropeFactory(levl_code=2, europecountry=es_country)

        assert user.has_perm("stats.view_report_stats", es_country)
        assert user.has_perm("stats.view_report_stats", subregion)

    def test_reviewer_can_view_areas_covered_by_workspace(
        self, user, es_country, country_workspace
    ):
        WorkspaceCollaborationGroupFactory(
            reviewers=[user], workspaces=[country_workspace]
        )
        subregion = NutsEuropeFactory(levl_code=2, europecountry=es_country)

        assert user.has_perm("stats.view_report_stats", es_country)
        assert user.has_perm("stats.view_report_stats", subregion)

    def test_subregion_workspace_only_grants_fully_covered_subregions(
        self, user, es_country
    ):
        workspace_geom = MultiPolygon(
            Polygon.from_bbox((-5.0, 38.0, -4.0, 39.0)), srid=4326
        )
        workspace = WorkspaceFactory(country=es_country, geom=workspace_geom)
        workspace.members.add(user)
        covered_area = NutsEuropeFactory(
            levl_code=2,
            europecountry=es_country,
            geom=MultiPolygon(Polygon.from_bbox((-4.9, 38.1, -4.1, 38.9)), srid=4326),
        )
        uncovered_area = NutsEuropeFactory(
            levl_code=2,
            europecountry=es_country,
            geom=MultiPolygon(Polygon.from_bbox((-3.5, 38.1, -3.1, 38.9)), srid=4326),
        )

        assert user.has_perm("stats.view_report_stats", covered_area)
        assert not user.has_perm("stats.view_report_stats", uncovered_area)
        assert not user.has_perm("stats.view_report_stats", es_country)

    def test_non_superuser_cannot_view_global_stats(self, user, country_workspace):
        country_workspace.members.add(user)

        assert not user.has_perm("stats.view_report_stats")
        assert not user.has_perm("stats.view_report_stats", None)

    def test_superuser_can_view_global_stats_and_geometryless_area(
        self, user, es_country
    ):
        user.is_superuser = True
        user.save()
        geometryless_area = NutsEuropeFactory(
            levl_code=2, europecountry=es_country, geom=None
        )

        assert user.has_perm("stats.view_report_stats")
        assert user.has_perm("stats.view_report_stats", geometryless_area)
