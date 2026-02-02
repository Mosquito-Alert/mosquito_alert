from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.db import models
from django.utils import timezone

from django_filters import rest_framework as filters

from rest_framework.exceptions import ValidationError
from rest_framework_gis.filterset import GeoFilterSet

from tigacrafting.models import IdentificationTask, ExpertReportAnnotation, Taxon, FavoritedReports
from tigaserver_app.models import Report, Notification, OWCampaigns, EuropeCountry, Photo

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


class TagFilter(filters.BaseInFilter, filters.CharFilter):
    pass

class BaseReportFilter(GeoFilterSet):
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
    tags = TagFilter(field_name='tags__name')

    geo_precision = filters.NumberFilter(method='filter_precision', min_value=0, label='Latitude/Longitude precision')
    def filter_precision(self, queryset, name, value):
        # Do nothing, will be used in the context
        return queryset

    boundary_uuid = filters.UUIDFilter(method='filter_by_boundary_uuid')
    def filter_by_boundary_uuid(self, queryset, name, value):
        cached_wkt = cache.get(str(value))
        if not cached_wkt:
            raise ValidationError("Boundary with the given UUID does not exist in cache.")
        try:
            geometry = GEOSGeometry(cached_wkt)
        except Exception:
            raise ValidationError("Failed to parse geometry from cached boundary WKT.")

        return queryset.filter(point__within=geometry)
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
    identification_taxon_ids = filters.ModelMultipleChoiceFilter(
        method='filter_identification_taxon_ids',
        queryset=Taxon.objects.all(),
        null_label="null",
        distinct=False
    )
    def filter_identification_taxon_ids(self, queryset, name, value):
        if not value:
            return queryset

        lookup = self.data.get("identification_taxon_ids_lookup")
        negate = self.data.get("negate_identification_taxon_ids") in ("true", "1", True)

        taxon_values = set()
        for taxon in value:
            if taxon == "null": # Must be the same a null_label
                taxon_values.add(None)
                continue

            if lookup == 'is_descendant_of':
                taxon_values.update(taxon.get_descendants())
            elif lookup == 'is_child_of':
                taxon_values.update(taxon.get_children())
            elif lookup == 'is_tree_of':
                taxon_values.update(Taxon.get_tree(taxon))
            else:
                taxon_values.add(taxon)

        if None in taxon_values:
            q = models.Q(identification_task__taxon__isnull=True) | models.Q(identification_task__taxon__in=taxon_values - {None})
        else:
            q = models.Q(identification_task__taxon__in=taxon_values)

        return queryset.exclude(q) if negate else queryset.filter(q)

    identification_taxon_ids_lookup = filters.ChoiceFilter(
        method='filter_do_nothing', 
        choices=[
            ('is_descendant_of', 'Is descendant of'),
            ('is_child_of', 'Is child of'),
            ('is_tree_of', 'Is tree of')
        ]
    )
    negate_identification_taxon_ids = filters.BooleanFilter(method='filter_do_nothing', label="Negate identification_taxon_ids filter")
    def filter_do_nothing(self, queryset, name, value):
        return queryset

class BiteFilter(BaseReportFilter):
    pass

class BreedingSiteFilter(BaseReportWithPhotosFilter):
    site_type = filters.MultipleChoiceFilter(
        choices=Report.BREEDING_SITE_TYPE_CHOICES,
        field_name='breeding_site_type'
    )

    has_water = filters.BooleanFilter(field_name='breeding_site_has_water')
    has_larvae = filters.BooleanFilter(field_name='breeding_site_has_larvae')
    has_near_mosquitoes = filters.BooleanFilter(field_name='breeding_site_has_near_mosquitoes')


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

    assignee_ids = filters.ModelMultipleChoiceFilter(
        field_name="assignees",
        queryset=User.objects.all(),
        method="filter_by_assignees"
    )

    def filter_by_assignees(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.assigned_to(users=value)

    fully_predicted = filters.BooleanFilter(
        method='filter_fully_predicted',
        help_text='Filters identification task based on whether all associated photos have predictions. Set to True to include identification tasks where every photo has a prediction; set to False to include identification tasks where at least one photo is missing a prediction.'
    )

    def filter_fully_predicted(self, queryset, name, value):
        # Subquery to check for existence of related Predictions
        photos_qs = Photo.objects.visible()

        return queryset.annotate(
            has_visible_photos=models.Exists(
                photos_qs.filter(
                    report=models.OuterRef('report')
                )
            ),
            has_missing_predictions=models.Exists(
                photos_qs.filter(
                    report=models.OuterRef('report')
                ).exclude(
                    prediction__identification_task=models.OuterRef('pk')
                )
            )
        ).filter(
            has_visible_photos=True,
            has_missing_predictions=not value
        )

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

    observation_country_ids = filters.ModelMultipleChoiceFilter(
        field_name="report__country",
        queryset=EuropeCountry.objects.all(),
    )

    result_taxon_ids = filters.ModelMultipleChoiceFilter(
        field_name="taxon",
        queryset=Taxon.objects.all(),
    )
    result_confidence = filters.RangeFilter(field_name="confidence")
    result_uncertainty = filters.RangeFilter(field_name="uncertainty")
    result_agreement = filters.RangeFilter(field_name="agreement")
    result_source = filters.MultipleChoiceFilter(
        choices=IdentificationTask.ResultSource.choices
    )

    review_action = filters.ChoiceFilter(
        choices=IdentificationTask.Review.choices,
        field_name="review_type",
        null_label="null",
        empty_label=None
    )

    class Meta:
        model = IdentificationTask
        fields = {
            "is_flagged": ["exact"],
            "is_safe": ["exact"],
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

    created_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="created", label="Created at"
    )
    updated_at = filters.IsoDateTimeFromToRangeFilter(
        field_name="last_modified", label="Updated at"
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

    is_favourite = filters.BooleanFilter(
        method="filter_by_is_favourite"
    )

    def filter_by_is_favourite(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.annotate(
            is_favourite=models.Exists(
                FavoritedReports.objects.filter(
                    user=models.OuterRef('user'),
                    report=models.OuterRef('report'),
                )
            )
        ).filter(is_favourite=value)

    type = filters.ChoiceFilter(
        choices=[('short', 'short'), ('long', 'long')],
        method="filter_by_type"
    )
    def filter_by_type(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(simplified_annotation=(value == 'short'))

    order_by = filters.OrderingFilter(
        fields=(("created", "created_at"), ("last_modified", "updated_at"))
    )

    class Meta:
        model = ExpertReportAnnotation
        fields = {}

class TaxonFilter(filters.FilterSet):
    rank = filters.MultipleChoiceFilter(
        choices=[(name.lower(), value) for name, value in zip(Taxon.TaxonomicRank.names, Taxon.TaxonomicRank.values)],
        method='filter_by_rank',
    )

    def filter_by_rank(self, queryset, name, value):
        # Map from name.lower() to actual values
        name_to_value = {name.lower(): val for name, val in zip(Taxon.TaxonomicRank.names, Taxon.TaxonomicRank.values)}
        mapped_values = [name_to_value.get(v) for v in value if v in name_to_value]
        return queryset.filter(rank__in=mapped_values)

    class Meta:
        model = Taxon
        fields = {
            "is_relevant": ["exact"],
        }