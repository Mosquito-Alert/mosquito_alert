from datetime import timedelta
from typing import Optional, Union
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from mosquito_alert.geo.models import Country
from mosquito_alert.stats.enums import (
    AreaLevel,
    NutsLevel,
    ReportStatsGroupBy,
    ReportStatsInterval,
)
from mosquito_alert.users.models import TigaUser
from mosquito_alert.workspaces.models import Workspace

TRUNC_FUNCS = {
    ReportStatsInterval.DAY: TruncDay,
    ReportStatsInterval.WEEK: TruncWeek,
    ReportStatsInterval.MONTH: TruncMonth,
}
NUTS_FK_FIELD = {NutsLevel.NUTS_2: "nuts_2_fk", NutsLevel.NUTS_3: "nuts_3_fk"}
STATS_MAX_ROWS = 10000


class ReportQuerySet(models.QuerySet):
    def has_photos(self, state: bool = True):
        from .models import Photo

        return self.annotate(
            photo_exist=models.Exists(
                Photo.objects.filter(report=models.OuterRef("pk")).visible()
            )
        ).filter(photo_exist=state)

    def deleted(self, state: bool = True):
        return self.filter(deleted_at__isnull=not state)

    def non_deleted(self):
        return self.deleted(state=False)

    def browsable(self, user: Optional[Union[User, TigaUser]] = None) -> QuerySet:
        from .models import Report

        # Should be the same as in is_browsable property.
        qs = self.non_deleted().filter(hide=False, location_is_masked=False)

        # Published for everyone.
        published_lookup = models.Q(
            published_at__isnull=False, published_at__lte=timezone.now()
        )
        if isinstance(user, User):
            has_view_perm = user.has_perm(
                "%(app_label)s.view_%(model_name)s"
                % {
                    "app_label": Report._meta.app_label,
                    "model_name": Report._meta.model_name,
                }
            )
            if has_view_perm:
                return qs

            countries_in_workspace = Country.objects.filter(
                workspaces__members=user,
                workspaces__geom__isnull=True,
            )

            lookup = models.Q()
            if countries_in_workspace.exists():
                lookup |= models.Q(country__in=countries_in_workspace)

            subregion_workspace = Workspace.objects.filter(
                members=user, geom__isnull=False
            )
            for workspace in subregion_workspace:
                lookup |= models.Q(
                    country=workspace.country,
                    point__within=workspace.geom,
                )

            if lookup:
                return qs.filter(published_lookup | lookup)

        if isinstance(user, TigaUser):
            return qs.filter(published_lookup | models.Q(user=user))

        return qs.filter(published_lookup)

    def with_finished_validation(self, state: bool = True) -> QuerySet:
        from mosquito_alert.identification_tasks.models import IdentificationTask

        return self.filter(
            models.Q(
                identification_task__status=IdentificationTask.Status.DONE,
                _negated=not state,
            )
        )

    def in_coarse_filter(self) -> QuerySet:
        from .models import Report
        from mosquito_alert.identification_tasks.models import IdentificationTask

        return (
            self.non_deleted()
            .filter(hide=False, location_is_masked=False)
            .filter(
                models.Q(published_at__isnull=True)
                | models.Q(published_at__gt=timezone.now())
            )
            .filter(
                models.Q(
                    models.Q(type=Report.TYPE_ADULT)
                    & models.Exists(
                        IdentificationTask.objects.filter(
                            report_id=models.OuterRef("pk")
                        ).new()
                    )
                )
                | models.Q(
                    models.Q(type=Report.TYPE_SITE)
                    & models.Exists(self.has_photos().filter(pk=models.OuterRef("pk")))
                )
            )
            .order_by("-server_upload_time")
        )

    # * ################## Report Stats ##################
    # --- Public-stats visibility -------------------------------------------------

    def publicly_visible(self) -> QuerySet:
        """Reports eligible to appear in public aggregate statistics.

        Narrower than `browsable()`: stats are anonymous/unauthenticated, so
        there's no per-user exception path, and only reports that have
        actually been published (not merely eligible for future publication)
        should be counted.
        """
        return self.non_deleted().filter(
            hide=False,
            location_is_masked=False,
            published_at__isnull=False,
        )

    # --- Aggregate stats -------------------------------------------------
    def stats(
        self,
        *,
        area: Optional[dict] = None,
        type: Optional[list] = None,
        date_from=None,
        date_to=None,
        group_by: set = frozenset(),
        interval: ReportStatsInterval = ReportStatsInterval.WEEK,
        cumulative: bool = True,
        level: NutsLevel = NutsLevel.NUTS_2,
    ) -> list:
        from .models import Report

        group_by = set(group_by)

        qs = self.publicly_visible().filter(type__in=Report.PUBLISHABLE_TYPES)
        if type:
            qs = qs.filter(type__in=type)
        if date_from:
            qs = qs.filter(server_upload_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(server_upload_time__date__lte=date_to)
        if area:
            qs = self._stats_filter_by_area(qs, area)

        values_fields = []

        if ReportStatsGroupBy.DATE in group_by:
            qs = qs.annotate(bucket=TRUNC_FUNCS[interval]("server_upload_time"))
            values_fields.append("bucket")

        region_field = None
        if ReportStatsGroupBy.REGION in group_by:
            region_field = NUTS_FK_FIELD[level]
            qs = qs.filter(**{f"{region_field}__isnull": False})
            values_fields += [
                f"{region_field}__gid",
                f"{region_field}__fid",
                f"{region_field}__name_latn",
            ]

        if ReportStatsGroupBy.TYPE in group_by:
            values_fields.append("type")

        rows_qs = (
            qs.values(*values_fields).annotate(count=Count("version_UUID")).order_by()
        )

        # ? Maybe this check is overkill?
        if len(list(rows_qs)) > STATS_MAX_ROWS:
            raise ValidationError(
                "This query would return too many rows. Narrow the date range, "
                "coarsen the interval, or scope to a smaller area."
            )

        rows = self._stats_reshape_rows(rows_qs, group_by, region_field)

        if ReportStatsGroupBy.DATE in group_by:
            rows = self._stats_zero_fill_dates(rows, interval, date_from, date_to)
            if cumulative:
                rows = self._stats_apply_cumulative(rows)
        else:
            rows.sort(key=lambda r: (r.get("region_name", ""), r.get("type", "")))

        return rows

    # --- Stats helpers (not copied onto the manager; internal use only) -------------------------------------------------
    def _stats_filter_by_area(self, qs, area):
        obj = area["obj"]
        if area["level"] == AreaLevel.COUNTRY:
            return qs.filter(country=obj)
        if area["level"] == AreaLevel.NUTS2:
            return qs.filter(nuts_2_fk=obj)
        if area["level"] == AreaLevel.NUTS3:
            return qs.filter(nuts_3_fk=obj)
        return qs

    def _stats_reshape_rows(self, rows_qs, group_by, region_field):
        reshaped = []
        for row in rows_qs:
            out = {}
            if ReportStatsGroupBy.DATE in group_by:
                out["date"] = row["bucket"].date().isoformat()
            if region_field:
                out["region_id"] = row[f"{region_field}__gid"]
                out["region_code"] = row[f"{region_field}__fid"]
                out["region_name"] = row[f"{region_field}__name_latn"]  # .split("/")[0]
            if ReportStatsGroupBy.TYPE in group_by:
                out["type"] = row["type"]
            out["count"] = row["count"]
            reshaped.append(out)
        return reshaped

    @staticmethod
    def _stats_truncate(d, interval):
        if interval == ReportStatsInterval.DAY:
            return d
        if interval == ReportStatsInterval.WEEK:
            return d - timedelta(days=d.weekday())
        return d.replace(day=1)

    @staticmethod
    def _stats_next_bucket(d, interval):
        if interval == ReportStatsInterval.DAY:
            return d + timedelta(days=1)
        if interval == ReportStatsInterval.WEEK:
            return d + timedelta(weeks=1)
        return (d.replace(day=28) + timedelta(days=4)).replace(day=1)

    def _stats_date_range(self, date_from, date_to, interval):
        if not date_from or not date_to:
            return []
        buckets = []
        current = self._stats_truncate(date_from, interval)
        end = self._stats_truncate(date_to, interval)
        while current <= end:
            buckets.append(current)
            current = self._stats_next_bucket(current, interval)
        return buckets

    def _stats_zero_fill_dates(self, rows, interval, date_from, date_to):
        if not date_from or not date_to:
            return sorted(rows, key=lambda r: r["date"])

        all_buckets = [
            d.isoformat() for d in self._stats_date_range(date_from, date_to, interval)
        ]

        series = {}
        for row in rows:
            key = tuple(
                sorted((k, v) for k, v in row.items() if k not in ("date", "count"))
            )
            series.setdefault(key, {})[row["date"]] = row["count"]
        if not series:
            series = {(): {}}

        filled = []
        for key, by_date in series.items():
            for bucket in all_buckets:
                out = dict(key)
                out["date"] = bucket
                out["count"] = by_date.get(bucket, 0)
                filled.append(out)

        filled.sort(
            key=lambda r: (r["date"], r.get("region_name", ""), r.get("type", ""))
        )
        return filled

    @staticmethod
    def _stats_apply_cumulative(rows):
        running = {}
        result = []
        for row in rows:
            key = tuple(
                sorted((k, v) for k, v in row.items() if k not in ("date", "count"))
            )
            running[key] = running.get(key, 0) + row["count"]
            result.append({**row, "count": running[key]})
        return result


ReportManager = models.Manager.from_queryset(ReportQuerySet)


class PhotoQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(hide=False)


PhotoManager = models.Manager.from_queryset(PhotoQuerySet)
