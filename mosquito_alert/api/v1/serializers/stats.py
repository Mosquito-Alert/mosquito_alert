from rest_framework import serializers

from mosquito_alert.geo.models import Country, NutsEurope
from mosquito_alert.reports.models import Report
from mosquito_alert.stats.enums import (
    AREA_LEVEL_ORDER,
    AreaLevel,
    NutsLevel,
    ReportStatsGroupBy,
    ReportStatsInterval,
)

# Report.TYPE_CHOICES minus `mission` — stats are about public report
# geography/counts, and 'mission' reports aren't part of that (see
# Report.PUBLISHABLE_TYPES). Kept as a derived constant, not a duplicated
# enum, so it can't drift from the model.
REPORT_STATS_TYPE_CHOICES = [
    choice for choice in Report.TYPE_CHOICES if choice[0] in Report.PUBLISHABLE_TYPES
]


# * #################### REQUEST ####################
# --- Area query param -------------------------------------------------
class AreaField(serializers.Field):
    """Parses `<level>:<id>`, e.g. `country:ES` or `nuts2:34`."""

    default_error_messages = {
        "invalid_format": 'Must be in the form "<level>:<id>", e.g. "country:ES" or "nuts2:34".',
        "invalid_level": 'Unknown area level "{level}". Must be one of: {levels}.',
        "invalid_id": '"{id}" is not a valid id for a {level} area.',
        "not_found": 'No {level} area found with id "{id}".',
    }

    def to_internal_value(self, data):
        if ":" not in data:
            self.fail("invalid_format")
        level, _, raw_id = data.partition(":")
        level = level.strip().lower()
        raw_id = raw_id.strip()

        if level not in AreaLevel.values:
            self.fail("invalid_level", level=level, levels=", ".join(AreaLevel.values))

        if level == AreaLevel.COUNTRY:
            obj = Country.objects.filter(iso2_code__iexact=raw_id).first()
            if obj is None:
                self.fail("not_found", level=level, id=raw_id)
            return {
                "level": AreaLevel.COUNTRY,
                "level_order": AREA_LEVEL_ORDER[AreaLevel.COUNTRY],
                "id": obj.iso2_code,
                "code": obj.iso3_code,
                "name": obj.name_engl,
                "obj": obj,
            }

        if not raw_id.isdigit():
            self.fail("invalid_id", id=raw_id, level=level)

        level_enum = AreaLevel(level)
        levl_code = NutsLevel.NUTS_2 if level == AreaLevel.NUTS2 else NutsLevel.NUTS_3
        obj = NutsEurope.objects.filter(pk=raw_id, levl_code=levl_code).first()
        if obj is None:
            self.fail("not_found", level=level, id=raw_id)
        return {
            "level": level_enum,
            "level_order": AREA_LEVEL_ORDER[level_enum],
            "id": obj.pk,
            "code": obj.fid,
            "name": obj.name,
            "obj": obj,
        }

    def to_representation(self, value):
        return {k: value[k] for k in ("level", "id", "code", "name")}


# --- Query params -------------------------------------------------
class ReportStatsQuerySerializer(serializers.Serializer):
    area = AreaField(required=False, allow_null=True, default=None)
    # type = serializers.MultipleChoiceField(choices=Report.TYPE_CHOICES.choices, required=False)
    type = serializers.MultipleChoiceField(
        choices=REPORT_STATS_TYPE_CHOICES, required=False
    )
    date_from = serializers.DateField(required=False, allow_null=True, default=None)
    date_to = serializers.DateField(required=False, allow_null=True, default=None)
    group_by = serializers.MultipleChoiceField(
        choices=ReportStatsGroupBy.choices, required=True, allow_empty=True
    )
    interval = serializers.ChoiceField(
        choices=ReportStatsInterval.choices,
        required=False,
        default=ReportStatsInterval.WEEK,
    )
    cumulative = serializers.BooleanField(required=False, default=False)
    level = serializers.ChoiceField(
        choices=NutsLevel.choices, required=False, default=NutsLevel.NUTS_2
    )

    def validate_type(self, value):
        return list(value)  # Plain strings, same as Report.type's underlying values

    def validate_group_by(self, value):
        return {ReportStatsGroupBy(v) for v in value}

    def validate_level(self, value):
        return NutsLevel(int(value))

    def validate(self, attrs):
        group_by, area = attrs["group_by"], attrs.get("area")
        date_from, date_to = attrs.get("date_from"), attrs.get("date_to")

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                {"date_to": "Must not be before `date_from`."}
            )

        if ReportStatsGroupBy.REGION in group_by:
            if area is None:
                raise serializers.ValidationError(
                    {"area": "`area` is required when grouping by region."}
                )
            if attrs["level"] <= area["level_order"]:
                raise serializers.ValidationError(
                    {"level": "`level` must be strictly finer than the area's level."}
                )

        return attrs


# * #################### RESPONSE ####################
# --- Meta response -------------------------------------------------
class AreaMetaSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=AreaLevel.choices)
    id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()


class ReportStatsMetaSerializer(serializers.Serializer):
    group_by = serializers.ListField(
        child=serializers.ChoiceField(
            choices=ReportStatsGroupBy.choices,
            # default=ReportStatsGroupBy.DATE # TODO: Make it default
        )
    )
    interval = serializers.ChoiceField(
        choices=ReportStatsInterval.choices, required=False
    )
    cumulative = serializers.BooleanField(required=False)
    level = serializers.ChoiceField(choices=NutsLevel.choices, required=False)
    area = AreaMetaSerializer(required=False, allow_null=True)


# --- Single flexible row/response shape -------------------------------------------------
class ReportStatsRowSerializer(serializers.Serializer):
    # All fields optional: which ones are actually present on a given row depends on the request's `group_by`.
    # Declared here so drf-spectacular can still document every possible key, even though the shape isn't
    # strictly polymorphic in the schema. Making this polymorphic would complicate the SDK generation.
    date = serializers.CharField(required=False)
    region_id = serializers.IntegerField(required=False)
    region_code = serializers.CharField(required=False)
    region_name = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=REPORT_STATS_TYPE_CHOICES, required=False)
    count = serializers.IntegerField()

    def to_representation(self, instance):
        # Only emit keys actually present on the row — don't pad with nulls for dimensions not in group_by.
        return dict(instance)


class ReportStatsResponseSerializer(serializers.Serializer):
    meta = ReportStatsMetaSerializer()
    data = ReportStatsRowSerializer(many=True)
