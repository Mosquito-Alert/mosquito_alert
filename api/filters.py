from django.db import models
from django.utils import timezone

from django_filters import rest_framework as filters

from tigaserver_app.models import Report, Notification, OWCampaigns, EuropeCountry


class CampaignFilter(filters.FilterSet):
    country_id = filters.ModelChoiceFilter(field_name="country_id", queryset=EuropeCountry.objects.all())
    is_active = filters.BooleanFilter(method="filter_is_active")

    order_by = filters.OrderingFilter(
        fields=(
            ("campaign_start_date", "start_date"),
            ("campaign_end_date", "end_date"),
        )
    )

    def filter_is_active(self, queryset, name, value):
        return queryset.filter(
            models.Q(
                models.Q(campaign_start_date__lte=timezone.now())
                & (
                    models.Q(campaign_end_date__isnull=True)
                    | models.Q(campaign_end_date__gt=timezone.now())
                ),
                _negated=not value,
            )
        )

    class Meta:
        model = OWCampaigns
        fields = ("country_id", "is_active")

class BaseReportFilter(filters.FilterSet):
    user_uuid = filters.UUIDFilter(field_name="user")
    short_id = filters.CharFilter(field_name="report_id", label="Short ID")
    created_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="creation_time", label="Created at"
    )
    received_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="server_upload_time", label="Received at"
    )
    updated_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="updated_at", label="Update at"
    )

    location_country_id = filters.ModelChoiceFilter(field_name="country_id", queryset=EuropeCountry.objects.all())
    location_nuts_3 = filters.CharFilter(field_name="nuts_3")
    location_nuts_2 = filters.CharFilter(field_name="nuts_2")

    order_by = filters.OrderingFilter(
        fields=(("server_upload_time", "received_at"), ("creation_time", "created_at"))
    )

    class Meta:
        model = Report
        fields = (
            "short_id",
            "created_at",
            "received_at",
            "updated_at",
            "location_country_id",
            "location_nuts_3",
            "location_nuts_2",
        )

class BaseReportWithPhotosFilter(BaseReportFilter):
    has_photos = filters.BooleanFilter(method='filter_has_photos', help_text='Has any photo')

    def filter_has_photos(self, queryset, name, value):
        # Subquery to check for existence of related Photos
        return queryset.has_photos(state=value)

    class Meta(BaseReportFilter.Meta):
        fields = BaseReportFilter.Meta.fields + ("has_photos",)


class ObservationFilter(BaseReportWithPhotosFilter):
    has_prediction = filters.BooleanFilter(
        method='filter_has_prediction',
        help_text='Filter observations that have an associated prediction. An observation is considered to have a prediction if a photo has been selected as reference to use the prediction from.'
    )
    has_predictions_all_photos = filters.BooleanFilter(
        method='filter_has_predictions_all_photos',
        help_text='Filters observations based on whether all associated photos have predictions. Set to True to include observations where every photo has a prediction; set to False to include observations where at least one photo is missing a prediction.'
    )

    def filter_has_prediction(self, queryset, name, value):
        # Subquery to check for existence of related Predictions
        return queryset.has_prediction(state=value)

    def filter_has_predictions_all_photos(self, queryset, name, value):
        # Subquery to check for existence of related Predictions
        return queryset.has_predictions_all_photos(state=value)

class BiteFilter(BaseReportFilter):
    pass

class BreedingSiteFilter(BaseReportWithPhotosFilter):
    pass


class NotificationFilter(filters.FilterSet):
    is_read = filters.BooleanFilter(method="filter_is_read")

    order_by = filters.OrderingFilter(fields=(("date_comment", "created_at"),))

    def filter_is_read(self, queryset, name, value):
        return queryset.seen_by_user(user=self.request.user, state=value)

    class Meta:
        model = Notification
        fields = ("is_read",)
