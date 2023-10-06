from typing import Any

from admin_numeric_filter.admin import NumericFilterModelAdmin, RangeNumericFilter, SliderNumericFilter
from django.contrib import admin
from django.db.models.query import QuerySet
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedGenericTabularInline, NestedModelAdmin, NestedTabularInline

from mosquito_alert.annotations.admin import (
    BaseAnnotationAdminMixin,
    BasePhotoAnnotationTaskAdminMixin,
    BaseShapeAdminMixin,
    BaseTaskAdminMixin,
)
from mosquito_alert.utils.admin import TimeStampedModelAdminMixin

from .forms import TaxonClassificationCandidateForm, TaxonClassificationCategorizedProbabilityCandidateForm
from .formsets import TaxonClassificationCandidateFormSet
from .models import (
    ExternalIdentification,
    IndividualIdentificationTask,
    IndividualIdentificationTaskResult,
    PhotoIdentificationTask,
    PhotoIdentificationTaskResult,
    Prediction,
    TaxonClassificationCandidate,
    UserIdentification,
)

##########################
# Candidates
##########################


class BaseTaxonAnnotationAdminMixin(BaseAnnotationAdminMixin):
    _taxon_annotation_fields = ("probability",)  # label already in BaseAnnotationAdminMixin

    fields = BaseAnnotationAdminMixin.fields + _taxon_annotation_fields
    list_display = BaseAnnotationAdminMixin.list_display + _taxon_annotation_fields
    list_filter = BaseAnnotationAdminMixin.list_filter + (("probability", SliderNumericFilter),)

    _taxon_annotation_fieldsets = (
        (
            _("Taxon classification"),
            {
                "fields": (fields,),
            },
        ),
    )

    class Media(NumericFilterModelAdmin.Media):
        pass


class TaxonClassificationCandidateAdminInline(BaseTaxonAnnotationAdminMixin, NestedGenericTabularInline):
    extra = 0
    is_sortable = False

    model = TaxonClassificationCandidate
    form = TaxonClassificationCandidateForm
    formset = TaxonClassificationCandidateFormSet

    fields = BaseTaxonAnnotationAdminMixin.fields + ("is_seed",)

    def get_queryset(self, request) -> QuerySet[Any]:
        # Only show seed candidates.
        return super().get_queryset(request).filter(is_seed=True)


class BaseClassificationAdminMixin:
    _classification_fields = ("sex",)

    _classification_tree_fieldsets = (
        (
            _("Classification tree"),
            {
                "fields": ("classification_tree",),
            },
        ),
    )
    _classification_fieldsets = (
        (
            _("Classification"),
            {
                "fields": _classification_fields,
            },
        ),
    )

    fields = _classification_fields
    readonly_fields = ("classification_tree",)

    @admin.display(description=_("Classification tree"))
    def classification_tree(self, obj) -> str:
        return format_html(
            "<textarea readonly>{}</textarea>", obj.get_classification_tree().get_tree_render() if obj else ""
        )


class BaseIdentificationAdminMixin(BaseClassificationAdminMixin, BaseShapeAdminMixin):
    fields = BaseShapeAdminMixin.fields + BaseClassificationAdminMixin.fields

    _identification_fieldset = (
        BaseShapeAdminMixin._shape_fieldsets + BaseClassificationAdminMixin._classification_fieldsets
    )


##########################
# Tasks
#########################


class BaseTaskWithResultsAdminMixin(BaseTaskAdminMixin):
    def has_add_permission(self, request, obj=None):
        return False

    def save_related(self, request: Any, form: Any, formsets: Any, change: Any) -> None:
        inlines_has_changes = any([x.has_changed() for x in formsets])

        result = super().save_related(request, form, formsets, change)

        if inlines_has_changes:
            form.instance.update_results()

        return result


class BaseTaskChildAdminMixin(TimeStampedModelAdminMixin):
    _task_child_fields = ("task",)

    fields = _task_child_fields + TimeStampedModelAdminMixin.fields
    readonly_fields = _task_child_fields + TimeStampedModelAdminMixin.readonly_fields


##########################
# Task Results
##########################


class BaseTaskResultAdminMixin(BaseTaskChildAdminMixin):
    _task_result_fields = ("type",)

    fields = (
        BaseTaskChildAdminMixin._task_child_fields + _task_result_fields + BaseTaskChildAdminMixin._timestamp_fields
    )

    _task_result_fieldsets = (
        (
            _("Task Result Information"),
            {
                "fields": BaseTaskChildAdminMixin._task_child_fields + _task_result_fields,
            },
        ),
    ) + BaseTaskChildAdminMixin._timestamp_fieldsets

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class BaseClassificationTaskResultAdminMixin(
    BaseTaskResultAdminMixin, BaseClassificationAdminMixin, BaseTaxonAnnotationAdminMixin
):
    fields = (
        BaseTaskResultAdminMixin._task_child_fields
        + BaseTaskResultAdminMixin._task_result_fields
        + BaseClassificationAdminMixin._classification_fields
        + BaseTaxonAnnotationAdminMixin.fields
        + BaseTaskResultAdminMixin._timestamp_fields
    )

    _classification_task_result_fieldsets = (
        BaseTaskResultAdminMixin._task_result_fieldsets
        + BaseTaxonAnnotationAdminMixin._taxon_annotation_fieldsets
        + BaseClassificationAdminMixin._classification_fieldsets
    )

    list_filter = (
        BaseTaskResultAdminMixin._task_result_fields
        + BaseClassificationAdminMixin._classification_fields
        + BaseTaxonAnnotationAdminMixin.list_filter
        + BaseTaskResultAdminMixin._timestamp_fields
    )


class BaseIdentificationTaskResultAdminMixin(BaseClassificationTaskResultAdminMixin, BaseShapeAdminMixin):
    fields = (
        BaseTaskResultAdminMixin._task_child_fields
        + BaseTaskResultAdminMixin._task_result_fields
        + BaseShapeAdminMixin.fields
        + BaseClassificationAdminMixin._classification_fields
        + BaseTaxonAnnotationAdminMixin.fields
        + BaseTaskResultAdminMixin._timestamp_fields
    )

    _identification_task_result_fieldsets = (
        BaseTaskResultAdminMixin._task_result_fieldsets
        + BaseShapeAdminMixin._shape_fieldsets
        + BaseTaxonAnnotationAdminMixin._taxon_annotation_fieldsets
        + BaseClassificationAdminMixin._classification_fieldsets
    )


@admin.register(IndividualIdentificationTaskResult)
class IndividualIdentificationTaskResultAdmin(BaseClassificationTaskResultAdminMixin, admin.ModelAdmin):
    fields = None
    fieldsets = (
        BaseClassificationTaskResultAdminMixin._classification_task_result_fieldsets
        + BaseClassificationTaskResultAdminMixin._classification_tree_fieldsets
    )
    list_display = BaseClassificationTaskResultAdminMixin.fields


class IndividualIdentificationTaskResultAdminInline(BaseClassificationTaskResultAdminMixin, NestedTabularInline):
    show_change_link = True

    model = IndividualIdentificationTaskResult


@admin.register(PhotoIdentificationTaskResult)
class PhotoIdentificationTaskResultAdmin(BaseIdentificationTaskResultAdminMixin, admin.ModelAdmin):
    _photo_identification_task_result_fields = (
        "user_identifications",
        "predictions",
        "external_identifications",
        "is_ground_truth",
    )

    __photo_identification_task_result_fieldsets = (
        (
            _("Result information"),
            {"fields": _photo_identification_task_result_fields},
        ),
    )

    fields = None
    fieldsets = (
        BaseTaskResultAdminMixin._task_result_fieldsets
        + __photo_identification_task_result_fieldsets
        + BaseShapeAdminMixin._shape_fieldsets
        + BaseTaxonAnnotationAdminMixin._taxon_annotation_fieldsets
        + BaseClassificationAdminMixin._classification_fieldsets
        + BaseIdentificationTaskResultAdminMixin._classification_tree_fieldsets
    )

    readonly_fields = BaseIdentificationTaskResultAdminMixin.readonly_fields + ("is_ground_truth",)

    list_display = (
        BaseTaskResultAdminMixin._task_child_fields
        + BaseTaskResultAdminMixin._task_result_fields
        + ("is_ground_truth",)
        + BaseClassificationAdminMixin._classification_fields
        + BaseTaxonAnnotationAdminMixin.fields
        + BaseTaskResultAdminMixin._timestamp_fields
    )
    list_filter = ("is_ground_truth",) + BaseIdentificationTaskResultAdminMixin.list_filter


class PhotoIdentificationTaskResultAdminInline(BaseIdentificationTaskResultAdminMixin, NestedTabularInline):
    _photo_identification_task_result_fields = ("is_ground_truth",)

    fields = BaseIdentificationTaskResultAdminMixin.fields + _photo_identification_task_result_fields
    readonly_fields = BaseIdentificationTaskResultAdminMixin.readonly_fields + _photo_identification_task_result_fields

    show_change_link = True
    model = PhotoIdentificationTaskResult


##########################
# Identifications
##########################
class BasePhotoIdentificationAdminMixin(BaseTaskChildAdminMixin, BaseIdentificationAdminMixin):
    extra = 0

    fields = BaseIdentificationAdminMixin.fields + BaseTaskChildAdminMixin.fields
    readonly_fields = BaseTaskChildAdminMixin.readonly_fields + BaseIdentificationAdminMixin.readonly_fields

    classes = ["collapse"]


class UserIdentificationAdminInline(BasePhotoIdentificationAdminMixin, NestedTabularInline):
    _user_identification_fields = (
        "user",
        "lead_time",
        "is_ground_truth",
        "was_skipped",
    )

    autocomplete_fields = ("user",)
    fields = _user_identification_fields + BasePhotoIdentificationAdminMixin.fields
    readonly_fields = BasePhotoIdentificationAdminMixin.readonly_fields + ("lead_time",)

    model = UserIdentification

    class UserIdentificationTaxonClassificationCandidateAdminInline(TaxonClassificationCandidateAdminInline):
        max_num = 1
        form = TaxonClassificationCategorizedProbabilityCandidateForm

    inlines = [UserIdentificationTaxonClassificationCandidateAdminInline]


class PredictionAdminInline(BasePhotoIdentificationAdminMixin, NestedTabularInline):
    model = Prediction

    inlines = [TaxonClassificationCandidateAdminInline]


class ExternalIdentificationAdminInline(BasePhotoIdentificationAdminMixin, NestedTabularInline):
    model = ExternalIdentification

    inlines = [TaxonClassificationCandidateAdminInline]


####################
# Tasks
####################
@admin.register(PhotoIdentificationTask)
class PhotoIdentificationTaskAdmin(BaseTaskWithResultsAdminMixin, BasePhotoAnnotationTaskAdminMixin, NestedModelAdmin):
    search_fields = ("photo__image",)

    fields = None
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "task",
                    ("photo", "preview"),
                    ("created_at", "updated_at"),
                    "is_completed",
                )
            },
        ),
        (
            _("Counters"),
            {
                "fields": (
                    "total_annotations",
                    "skipped_annotations",
                    "total_predictions",
                    "total_external",
                )
            },
        ),
    )

    readonly_fields = (
        "task",
        "total_external",
        "photo",
    ) + BasePhotoAnnotationTaskAdminMixin.readonly_fields

    list_display = (
        "photo",
        "total_annotations",
        "skipped_annotations",
        "total_predictions",
        "total_external",
        "is_completed",
        "created_at",
        "updated_at",
    )
    list_filter = (
        ("total_annotations", RangeNumericFilter),
        ("skipped_annotations", RangeNumericFilter),
        ("total_predictions", RangeNumericFilter),
        ("total_external", RangeNumericFilter),
        "is_completed",
        "created_at",
        "updated_at",
    )

    inlines = [
        PhotoIdentificationTaskResultAdminInline,
        UserIdentificationAdminInline,
        PredictionAdminInline,
        ExternalIdentificationAdminInline,
    ]

    @admin.display(description=_("Photo preview"))
    def preview(self, obj):
        if obj.pk:
            return format_html(f"<img src='{obj.photo.image.url}' height='150' />")
        return "Upload image for preview"

    class Media(NumericFilterModelAdmin.Media):
        pass


class PhotoIdentificationTaskAdminInline(
    BaseTaskWithResultsAdminMixin, BasePhotoAnnotationTaskAdminMixin, NestedTabularInline
):
    fields = (
        "task",
        "photo",
        "total_annotations",
        "skipped_annotations",
        "total_predictions",
        "total_external",
        "is_completed",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "task",
        "total_external",
        "photo",
    ) + BasePhotoAnnotationTaskAdminMixin.readonly_fields

    model = PhotoIdentificationTask
    is_sortable = False
    extra = 0
    classes = ["collapse"]
    show_change_link = True

    inlines = [PhotoIdentificationTaskResultAdminInline]


@admin.register(IndividualIdentificationTask)
class IndividualIdentificationTaskAdmin(BaseTaskWithResultsAdminMixin, NestedModelAdmin):
    fields = ("individual", ("is_locked", "is_completed"), ("created_at", "updated_at"))
    readonly_fields = ("individual",) + BaseTaskWithResultsAdminMixin.readonly_fields

    list_display = ("individual", "is_locked", "is_completed", "created_at", "updated_at")
    list_filter = ("is_locked", "is_completed", "created_at", "updated_at")

    inlines = [IndividualIdentificationTaskResultAdminInline, PhotoIdentificationTaskAdminInline]


class IndividualIdentificationTaskAdminInline(BaseTaskWithResultsAdminMixin, NestedTabularInline):
    is_sortable = False
    extra = 0
    model = IndividualIdentificationTask
    show_change_link = True

    fields = ("is_locked",) + BaseTaskWithResultsAdminMixin.fields

    inlines = [IndividualIdentificationTaskResultAdminInline, PhotoIdentificationTaskAdminInline]
