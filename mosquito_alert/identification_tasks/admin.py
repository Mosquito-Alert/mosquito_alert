from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter

from .models import ExpertReportAnnotation, IdentificationTask, PhotoPrediction


class ExpertReportAnnotationInlineAdmin(admin.StackedInline):
    model = ExpertReportAnnotation

    ordering = ('last_modified',)
    fields = (
        'user',
        ('is_finished', 'decision_level', 'is_simplified'),
        ("taxon", "confidence"),
        ("sex", "is_blood_fed", "is_gravid"),
        'status',
        'best_photo',
        ('public_note', 'message_for_user'),
        ('created', 'last_modified')
    )
    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only by getting the model's fields dynamically
        return [field.name for field in self.model._meta.fields]

    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class PhotoPredictionInlineAdmin(admin.StackedInline):
    model = PhotoPrediction

    ordering = ('created_at',)
    fields = (
        'photo',
        ('taxon', 'is_decisive', 'confidence', 'uncertainty'),
        ('insect_confidence', 'predicted_class', 'threshold_deviation'),
        'classifier_version',
        ('x_tl', 'x_br', 'y_tl', 'y_br'),
        tuple(PhotoPrediction.get_score_fieldnames()),
        ('created_at', 'updated_at')
    )
    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only by getting the model's fields dynamically
        return [field.name for field in self.model._meta.fields] + ['confidence', 'uncertainty']

    def confidence(self, obj):
        return obj.confidence

    def uncertainty(self, obj):
        return obj.uncertainty

    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(IdentificationTask)
class IdentificationTaskAdmin(NumericFilterModelAdmin):
    search_fields = ("report__pk", "taxon__name")
    list_display = ("report", "status", "is_safe", "is_flagged", 'total_annotations', 'total_finished_annotations', 'taxon', 'confidence', 'created_at')
    list_filter = (
        "status",
        ("is_safe", admin.BooleanFieldListFilter),
        ("is_flagged", admin.BooleanFieldListFilter),
        'total_finished_annotations',
        ('confidence', SliderNumericFilter),
        ('uncertainty', SliderNumericFilter),
        ('taxon', admin.RelatedOnlyFieldListFilter),
        ('report__country', admin.RelatedOnlyFieldListFilter)
    )
    ordering = ('-created_at',)
    fields = (
        ("report", "photo"),
        ("created_at", "updated_at"),
        ("status", "is_safe", "is_flagged"),
        ("exclusivity_end", "in_exclusivity_period"),
        ("total_annotations", "total_finished_annotations"),
        ("review_type", "reviewed_at"),
        ("taxon", "confidence_label", "confidence"),
        ("agreement", "uncertainty"),
        "public_note",
        "message_for_user"
    )

    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only by getting the model's fields dynamically
        return [field.name for field in self.model._meta.fields] + ['exclusivity_end', 'in_exclusivity_period', "confidence_label"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('report__country', 'taxon', 'photo').prefetch_related('expert_report_annotations', 'photo_predictions')

    inlines = [
        ExpertReportAnnotationInlineAdmin,
        PhotoPredictionInlineAdmin
    ]