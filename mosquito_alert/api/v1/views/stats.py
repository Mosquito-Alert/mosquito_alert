from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.response import Response

from mosquito_alert.api.v1.serializers.stats import (
    REPORT_STATS_TYPE_CHOICES,
    ReportStatsQuerySerializer,
    ReportStatsResponseSerializer,
)
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.reports.models import Report
from mosquito_alert.stats.enums import (
    NutsLevel,
    ReportStatsGroupBy,
    ReportStatsInterval,
)

# Query params that may legitimately be comma-separated single values
# (e.g. ?type=bite,adult) rather than repeated (?type=bite&type=adult).
CSV_PARAMS = ("type", "group_by")


@extend_schema_view(
    list=extend_schema(
        description="Aggregated report counts (for displaying data tables or charts, for example). "
        "The keys present on each row of `data` depend on `group_by` (always includes `count`, "
        "plus `date` if grouped by date, `region_id`/`region_code`/`region_name` "
        "if grouped by region, and `type` if grouped by type).",
        parameters=[
            OpenApiParameter(
                "area",
                str,
                description='"\<level\>:\<id\>", e.g. "country:ES" or "nuts2:34".',
            ),
            OpenApiParameter(
                name="type",
                type={
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [value for value, _ in REPORT_STATS_TYPE_CHOICES],
                    },
                },
                location=OpenApiParameter.QUERY,
                required=False,
                style="form",
                explode=False,
                description="Comma-separated subset of: "
                + ", ".join(v for v, _ in REPORT_STATS_TYPE_CHOICES)
                + ".",
            ),
            OpenApiParameter("date_from", str),
            OpenApiParameter("date_to", str),
            OpenApiParameter(
                name="group_by",
                type={
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ReportStatsGroupBy.values,
                    },
                },
                location=OpenApiParameter.QUERY,
                required=False,
                style="form",
                explode=False,  # Ensures the array is passed as a comma-separated list rather than repeated parameters
                description=f"Comma-separated subset of: {', '.join(ReportStatsGroupBy.values)}.",
            ),
            OpenApiParameter(
                "interval",
                str,
                enum=ReportStatsInterval.values,
                description="The interval at which to aggregate data when grouping by date. Defaults to week.",
            ),
            OpenApiParameter(
                "cumulative",
                bool,
                description="Whether to return cumulative counts over time. It only applies when grouping by date. Defaults to False.",
            ),
            OpenApiParameter(
                "level",
                int,
                enum=NutsLevel.values,
                description="The NUTS level to aggregate by when grouping by region. Defaults to NUTS 2.",
            ),
        ],
        responses={200: ReportStatsResponseSerializer},
    )
)
class ReportStatsViewSet(GenericViewSet):
    queryset = Report.objects.none()

    def list(self, request, *args, **kwargs):
        query_serializer = ReportStatsQuerySerializer(
            data=self._normalize_query_params(request)
        )
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        data = Report.objects.stats(
            area=params["area"],
            type=params.get("type"),
            date_from=params.get("date_from"),
            date_to=params.get("date_to"),
            group_by=params["group_by"],
            interval=params["interval"],
            cumulative=params["cumulative"],
            level=params["level"],
        )

        meta = {
            "group_by": sorted(params["group_by"]),
            "area": query_serializer.fields["area"].to_representation(params["area"])
            if params["area"]
            else None,
        }
        if ReportStatsGroupBy.DATE in params["group_by"]:
            meta["interval"] = params["interval"]
            meta["cumulative"] = params["cumulative"]
        if ReportStatsGroupBy.REGION in params["group_by"]:
            meta["level"] = params["level"]

        response_serializer = ReportStatsResponseSerializer(
            {"meta": meta, "data": data}
        )
        return Response(response_serializer.data)

    @staticmethod
    def _normalize_query_params(request):
        data = {}
        for key in request.query_params:
            values = request.query_params.getlist(key)
            if key in CSV_PARAMS and len(values) == 1:
                data[key] = values[0].split(",") if values[0] else []
            elif len(values) == 1:
                data[key] = values[0]
            else:
                data[key] = values
        return data
