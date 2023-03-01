from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedTabularInline

from .models import (
    IdentifierUserProfile,
    ImageTaxonPrediction,
    ImageTaxonPredictionRun,
    UserIdentificationSuggestion,
)


##########################
# Photo-related admin inlines
##########################
class ImageTaxonPredictionAdminInline(NestedTabularInline):
    is_sortable = False

    extra = 0
    model = ImageTaxonPrediction


class ImageTaxonPredictionRunAdminInline(NestedStackedInline):
    is_sortable = False

    extra = 0
    model = ImageTaxonPredictionRun
    inlines = [ImageTaxonPredictionAdminInline]


##########################
# Individual-related admin inlines
##########################
class UserIdentificationSuggestionInline(NestedStackedInline):
    is_sortable = False

    model = UserIdentificationSuggestion
    extra = 0
    fieldsets = (
        (None, {"fields": ("user_profile", ("taxon", "probability"), "notes")}),
        (
            _("Probability tree"),
            {"classes": ("collapse",), "fields": ("show_prob_tree",)},
        ),
    )
    readonly_fields = ["show_prob_tree"]

    def show_prob_tree(self, instance):
        if instance:
            render = UserIdentificationSuggestion.get_probability_tree(
                individual=instance.individual, user_profile=instance.user_profile
            ).get_tree_render()
            return format_html("<textarea readonly>{}</textarea>", render)

    show_prob_tree.short_description = _("Probability tree")


##########################
# User-related admin
##########################
class IdentifierUserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_superexpert")
    list_filter = ("is_superexpert",)


admin.site.register(IdentifierUserProfile, IdentifierUserProfileAdmin)
