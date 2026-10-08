import rules
from django.db.models import Q
from django.apps import apps

from mosquito_alert.geo.models import Country, NutsEurope
from mosquito_alert.workspaces.models import Workspace

STATS_APP_LABEL = apps.get_app_config("stats").label

# ~1 km in degrees (SRID 4326). Absorbs boundary mismatches between datasets.
GEOM_TOLERANCE = 0.01


@rules.predicate
def is_superuser(user):
    # The only hardcoded bypass — built into the User model, nothing to assign.
    return user.is_superuser


@rules.predicate
def can_view_report_stats_for_area(user, obj):
    """`obj` is the Country or NutsEurope instance the stats were requested for (both expose `.geom`),
    or None for an unscoped/global request.

    Access is derived purely from workspace membership (any role) and collaboration-group reviewer status
    — no assignable permission involved. A workspace grants access to an area if its coverage geometrically
    covers the requested area:
      - geom=None workspace covers its whole country (and any subdivision)
      - geom set covers only areas within that polygon
    """
    if obj is None or obj.geom is None:
        return False

    workspaces = Workspace.objects.filter(
        Q(memberships__user=user) | Q(collaboration_groups__reviewers=user)
    ).distinct()

    # Country that the requested area belongs to.
    if isinstance(obj, Country):
        area_country_id = obj.pk
    elif isinstance(obj, NutsEurope):
        area_country_id = obj.europecountry_id
    else:
        return False

    # 1. Country-wide workspaces: match through the hierarchy, no geometry.
    if (
        area_country_id is not None
        and workspaces.filter(geom__isnull=True, country_id=area_country_id).exists()
    ):
        return True

    # 2. Sub-region workspaces: only grant subdivisions that fit inside the
    #    workspace polygon. A whole country is never covered by a sub-region.
    if isinstance(obj, NutsEurope) and obj.geom is not None:
        for workspace in workspaces.filter(geom__isnull=False):
            if workspace.geom.buffer(GEOM_TOLERANCE).covers(obj.geom):
                return True

    return False


VIEW_REPORT_STATS_PERM = f"{STATS_APP_LABEL}.view_report_stats"
rules.add_perm(
    VIEW_REPORT_STATS_PERM,
    is_superuser | can_view_report_stats_for_area,
)
