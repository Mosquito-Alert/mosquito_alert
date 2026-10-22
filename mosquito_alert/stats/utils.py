from mosquito_alert.geo.models import Country, NutsEurope
from mosquito_alert.workspaces.models import Workspace, WorkspaceMembership
from django.db.models import Q


# ~1 km in degrees (SRID 4326). Absorbs boundary mismatches between datasets.
GEOM_TOLERANCE = 0.01

_NUTS_ONLY = ("gid", "fid", "name_latn", "levl_code", "europecountry_id")  # skip geom


def user_workspaces(user):
    return Workspace.objects.filter(
        Q(memberships__user=user) | Q(collaboration_groups__reviewers=user)
    ).distinct()


# * ############## GET ACCESSIBLE AREAS (Tree object) ##############
def _nuts_node(region, is_member=False):
    level = f"nuts{region.levl_code}"
    return {
        "key": f"{level}:{region.pk}",
        "level": level,
        "id": str(region.pk),
        "code": region.fid,
        "name": region.name,
        "is_member": is_member,
        "children": [],
    }


def _parent_fid(region):
    # NUTS3 codes extend their NUTS2 code (ES511 -> ES51). There is no FK for this.
    return region.fid[:4] if region.levl_code == 3 else None


def _build_forest(regions, member_fids=frozenset()):
    nodes = {r.fid: _nuts_node(r, r.fid in member_fids) for r in regions}
    roots = []
    for region in sorted(regions, key=lambda r: r.fid):
        parent = nodes.get(_parent_fid(region))
        (parent["children"] if parent else roots).append(nodes[region.fid])
    return roots


# Get the accessible area tree for the given user.
# It builds a tree of accessible areas, with countries as top-level nodes and NUTS regions as children.
# Also, it adds an "is_member" flag to indicate if the user is a member of the workspace covering that area.
# It handles country-wide and geographically bounded workspaces separately. A workspace with no geometry grants access
# to its country and its NUTS2/NUTS3 subdivisions. A workspace with geometry includes regions whose geometries are
# covered by the workspace geometry after applying a tolerance buffer. Regions already represented under a country-wide workspace are excluded from this second group.
def get_accessible_area_tree(user):
    from .rules import UNRESTRICTED_PERM

    if user.is_superuser or user.has_perm(UNRESTRICTED_PERM):
        workspaces = Workspace.objects.all()
    else:
        workspaces = user_workspaces(user)
    workspaces = list(workspaces.only("id", "country_id", "geom"))
    if not workspaces:
        return []

    member_ids = set(
        WorkspaceMembership.objects.filter(user=user).values_list(
            "workspace_id", flat=True
        )
    )

    # 1. Country-wide workspaces (geom is NULL): country + all its subdivisions.
    country_wide = {}  # country_id -> is_member
    for ws in workspaces:
        if ws.geom is None and ws.country_id:
            country_wide[ws.country_id] = (
                country_wide.get(ws.country_id, False) or ws.pk in member_ids
            )

    tree = []
    if country_wide:
        regions_by_country = {}
        for region in NutsEurope.objects.filter(
            europecountry_id__in=country_wide, levl_code__in=(2, 3)
        ).only(*_NUTS_ONLY):
            regions_by_country.setdefault(region.europecountry_id, []).append(region)

        for country in Country.objects.filter(pk__in=country_wide).only(
            "id", "iso2_code", "iso3_code", "name_engl"
        ):
            if not country.iso2_code:  # Skip countries without an ISO2 code
                continue
            node = {
                "key": f"country:{country.iso2_code}",
                "level": "country",
                "id": country.iso2_code,
                "code": country.iso3_code,
                "name": country.name_engl,
                "is_member": country_wide[country.pk],
                "children": [],
            }
            node["children"] = _build_forest(regions_by_country.get(country.pk, []))
            tree.append(node)

    # 2. Sub-region workspaces (geom set): the NUTS regions inside the polygon.
    matched, member_fids = {}, set()
    for ws in workspaces:
        if ws.geom is None:
            continue
        regions = list(
            NutsEurope.objects.filter(
                levl_code__in=(2, 3),
                geom__coveredby=ws.geom.buffer(GEOM_TOLERANCE),
            )
            .exclude(europecountry_id__in=country_wide)  # already in a country tree
            .only(*_NUTS_ONLY)
        )
        fids = {r.fid for r in regions}
        matched.update({r.fid: r for r in regions})
        if ws.pk in member_ids:
            # Mark only this workspace's top-level regions, not their children.
            member_fids |= {r.fid for r in regions if _parent_fid(r) not in fids}

    tree.extend(_build_forest(list(matched.values()), member_fids))
    return sorted(tree, key=lambda n: n["name"])
