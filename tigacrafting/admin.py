from django.contrib import admin
from tigacrafting.models import ExpertReportAnnotation, UserStat, Taxon, IdentificationTask, PhotoPrediction
from tigaserver_app.models import NutsEurope
from django.utils.translation import gettext_lazy as _

from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from modeltranslation.admin import TranslationAdmin


class ExpertReportAnnotationInlineAdmin(admin.StackedInline):
    model = ExpertReportAnnotation

    ordering = ('last_modified',)
    fields = (
        'user',
        ('validation_complete', 'revise'),
        ('validation_complete_executive', 'simplified_annotation'),
        ('category', 'complex', 'other_species', 'validation_value'),
        ("taxon", "confidence"),
        ("sex", "is_blood_fed", "is_gravid"),
        'status',
        'best_photo',
        ('edited_user_notes', 'message_for_user'),
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

class UserStatAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    ordering = ('user__username',)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "nuts2_assignation":
            kwargs["queryset"] = NutsEurope.objects.all().order_by('europecountry__name_engl','name_latn')
        return super(UserStatAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Taxon)
class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name", 'content_object', 'is_relevant')
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon)

    fieldsets = [
        (_("Node position"), {"fields": ("_position", "_ref_node_id")}),
        (_("Basic information"), {"fields": ("rank", ("name", "is_relevant"), "common_name")}),
        (_("Old tables relationship"), {"fields": ("content_type", "object_id")})
    ]

admin.site.register(UserStat, UserStatAdmin)
