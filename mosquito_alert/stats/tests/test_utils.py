import pytest
from django.contrib.gis.geos import MultiPolygon, Polygon

from mosquito_alert.geo.tests.factories import CountryFactory, NutsEuropeFactory
from mosquito_alert.stats.utils import get_accessible_area_tree
from mosquito_alert.users.tests.factories import UserFactory
from mosquito_alert.workspaces.tests.factories import (
    WorkspaceCollaborationGroupFactory,
    WorkspaceFactory,
)


def _country(iso2_code, name):
    return CountryFactory(
        iso2_code=iso2_code,
        iso3_code=f"{iso2_code}X",
        name_engl=name,
        geom=MultiPolygon(Polygon.from_bbox((0, 0, 10, 10)), srid=4326),
    )


def _region(country, level, fid, name, bounds=(1, 1, 4, 4)):
    return NutsEuropeFactory(
        levl_code=level,
        fid=fid,
        europecountry=country,
        name_latn=name,
        geom=MultiPolygon(Polygon.from_bbox(bounds), srid=4326),
    )


@pytest.mark.django_db
def test_get_accessible_area_tree_returns_empty_for_user_without_workspaces():
    user = UserFactory()

    assert get_accessible_area_tree(user) == []


@pytest.mark.django_db
def test_get_accessible_area_tree_builds_country_hierarchy_for_members():
    user = UserFactory()
    country = _country("AA", "Accessible country")
    workspace = country.workspaces.get(geom__isnull=True)
    workspace.members.add(user)
    nuts2 = _region(country, 2, "AA11", "Area")
    nuts3 = _region(country, 3, "AA111", "Subarea")
    other_nuts3 = _region(country, 3, "AA112", "Other subarea")

    tree = get_accessible_area_tree(user)

    assert tree == [
        {
            "key": "country:AA",
            "level": "country",
            "id": "AA",
            "code": "AAX",
            "name": "Accessible country",
            "is_member": True,
            "children": [
                {
                    "key": f"nuts2:{nuts2.pk}",
                    "level": "nuts2",
                    "id": str(nuts2.pk),
                    "code": "AA11",
                    "name": "Area",
                    "is_member": False,
                    "children": [
                        {
                            "key": f"nuts3:{nuts3.pk}",
                            "level": "nuts3",
                            "id": str(nuts3.pk),
                            "code": "AA111",
                            "name": "Subarea",
                            "is_member": False,
                            "children": [],
                        },
                        {
                            "key": f"nuts3:{other_nuts3.pk}",
                            "level": "nuts3",
                            "id": str(other_nuts3.pk),
                            "code": "AA112",
                            "name": "Other subarea",
                            "is_member": False,
                            "children": [],
                        },
                    ],
                }
            ],
        }
    ]


@pytest.mark.django_db
def test_get_accessible_area_tree_includes_only_regions_covered_by_subregion_workspace():
    user = UserFactory()
    country = _country("BB", "Bounded country")
    workspace_geom = MultiPolygon(Polygon.from_bbox((1, 1, 5, 5)), srid=4326)
    WorkspaceFactory(country=None, geom=workspace_geom, members=[user])
    covered_nuts2 = _region(country, 2, "BB11", "Covered area", (2, 2, 4, 4))
    covered_nuts3 = _region(country, 3, "BB111", "Covered subarea", (2, 2, 3, 3))
    _region(country, 2, "BB12", "Outside area", (7, 7, 8, 8))

    tree = get_accessible_area_tree(user)

    assert tree == [
        {
            "key": f"nuts2:{covered_nuts2.pk}",
            "level": "nuts2",
            "id": str(covered_nuts2.pk),
            "code": "BB11",
            "name": "Covered area",
            "is_member": True,
            "children": [
                {
                    "key": f"nuts3:{covered_nuts3.pk}",
                    "level": "nuts3",
                    "id": str(covered_nuts3.pk),
                    "code": "BB111",
                    "name": "Covered subarea",
                    "is_member": False,
                    "children": [],
                }
            ],
        }
    ]


@pytest.mark.django_db
def test_get_accessible_area_tree_includes_collaboration_reviewer_areas():
    user = UserFactory()
    country = _country("CC", "Reviewer country")
    workspace = country.workspaces.get(geom__isnull=True)
    WorkspaceCollaborationGroupFactory(workspaces=[workspace], reviewers=[user])

    tree = get_accessible_area_tree(user)

    assert len(tree) == 1
    assert tree[0]["key"] == "country:CC"
    assert tree[0]["is_member"] is False


@pytest.mark.django_db
def test_get_accessible_area_tree_includes_all_workspaces_for_superuser():
    user = UserFactory(is_superuser=True)
    country = _country("DD", "Unrestricted country")
    nuts2 = _region(country, 2, "DD11", "Unrestricted area")

    tree = get_accessible_area_tree(user)

    assert tree == [
        {
            "key": "country:DD",
            "level": "country",
            "id": "DD",
            "code": "DDX",
            "name": "Unrestricted country",
            "is_member": False,
            "children": [
                {
                    "key": f"nuts2:{nuts2.pk}",
                    "level": "nuts2",
                    "id": str(nuts2.pk),
                    "code": "DD11",
                    "name": "Unrestricted area",
                    "is_member": False,
                    "children": [],
                }
            ],
        }
    ]
