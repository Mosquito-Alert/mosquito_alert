from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from django_filters import rest_framework as filters

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation, Taxon
from tigaserver_app.models import Report, Notification, OWCampaigns, EuropeCountry

User = get_user_model()

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
            "country_id"
        )

class BaseReportWithPhotosFilter(BaseReportFilter):
    has_photos = filters.BooleanFilter(method='filter_has_photos', help_text='Has any photo')

    def filter_has_photos(self, queryset, name, value):
        # Subquery to check for existence of related Photos
        return queryset.has_photos(state=value)

    class Meta(BaseReportFilter.Meta):
        fields = BaseReportFilter.Meta.fields + ("has_photos",)


class ObservationFilter(BaseReportWithPhotosFilter):
    identification_taxon = filters.ModelMultipleChoiceFilter(
        field_name="identification_task__taxon",
        queryset=Taxon.objects.all(),
    )

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

class IdentificationTaskFilter(filters.FilterSet):
    annotator_ids = filters.ModelMultipleChoiceFilter(
        field_name="assignees",
        queryset=User.objects.all(),
        method="filter_by_annotators"
    )

    def filter_by_annotators(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotated_by(users=value)

    num_assignations = filters.RangeFilter(field_name="total_annotations")
    num_annotations = filters.RangeFilter(field_name="total_finished_annotations")

    created_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="created_at", label="Created at"
    )
    updated_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="updated_at", label="Update at"
    )

    order_by = filters.OrderingFilter(
        fields=("created_at", "updated_at")
    )

    status = filters.MultipleChoiceFilter(
        choices=IdentificationTask.Status.choices
    )

    observation_country = filters.ModelMultipleChoiceFilter(
        field_name="report__country",
        queryset=EuropeCountry.objects.all(),
    )

    result_taxon = filters.ModelMultipleChoiceFilter(
        field_name="taxon",
        queryset=Taxon.objects.all(),
    )
    result_confidence = filters.RangeFilter(field_name="confidence")
    result_uncertainty = filters.RangeFilter(field_name="uncertainty")
    result_agreement = filters.RangeFilter(field_name="agreement")

    class Meta:
        model = IdentificationTask
        fields = {
            "is_flagged": ["exact"],
            "is_safe": ["exact"],
            "review_type": ["exact"],
        }

class AnnotationFilter(filters.FilterSet):
    user_ids = filters.ModelMultipleChoiceFilter(
        field_name="user",
        queryset=User.objects.all(),
    )

    classification_taxon_ids = filters.ModelMultipleChoiceFilter(
        field_name="taxon",
        queryset=Taxon.objects.all(),
    )

    classification_confidence = filters.RangeFilter(field_name="confidence")
    classification_confidence_label = filters.ChoiceFilter(
        choices=[('definitely', 'definitely'), ('probably', 'probably')],
        method="filter_by_confidence_label"
    )

    def filter_by_confidence_label(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_DEFINITELY if value == 'definitely' else ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY
        )

    is_flagged = filters.BooleanFilter(
        method="filter_by_is_flagged"
    )

    def filter_by_is_flagged(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            status=ExpertReportAnnotation.STATUS_FLAGGED
        )

    is_decisive = filters.BooleanFilter(
        method="filter_by_is_decisive"
    )

    def filter_by_is_decisive(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            models.Q(
                models.Q(revise=True)
                | models.Q(validation_complete_executive=True),
                _negated=not value
            )
        )

    order_by = filters.OrderingFilter(
        fields=("created_at", "updated_at")
    )

    class Meta:
        model = ExpertReportAnnotation
        fields = {}

class TaxonFilter(filters.FilterSet):
    class Meta:
        model = Taxon
        fields = {
            "is_relevant": ["exact"],
        }