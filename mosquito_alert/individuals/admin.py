from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedTabularInline
from nested_admin.polymorphic import NestedPolymorphicModelAdmin

from mosquito_alert.identifications.admin import UserIdentificationSuggestionInline
from mosquito_alert.identifications.models import (
    CommunityIdentificationResult,
    ComputerVisionIdentificationSuggestion,
    EnsembledIdentificationResult,
)
from mosquito_alert.images.admin import m2mPhotoAdminInlineMixin

from .models import Individual


class ReadOnlyPhotoAdminInline(m2mPhotoAdminInlineMixin, NestedTabularInline):
    model = Individual.photos.through
    is_sortable = False


class IndividualAdmin(NestedPolymorphicModelAdmin):
    list_display = ["__str__", "is_identified", "thumbnail"]
    list_filter = [("taxon", admin.RelatedOnlyFieldListFilter), "is_identified"]
    fieldsets = (
        (None, {"fields": (("taxon", "get_is_identified"),)}),
        (
            _("Probability trees"),
            {
                "classes": ("collapse",),
                "fields": (
                    "show_result_prob_tree",
                    ("show_computervision_prob_tree", "show_community_prob_tree"),
                ),
            },
        ),
    )
    readonly_fields = [
        "taxon",
        "get_is_identified",
        "show_result_prob_tree",
        "show_community_prob_tree",
        "show_computervision_prob_tree",
    ]
    inlines = [
        ReadOnlyPhotoAdminInline,
        UserIdentificationSuggestionInline,
    ]

    def get_is_identified(self, instance):
        return instance.is_identified

    get_is_identified.boolean = True
    get_is_identified.short_description = "Is identified"

    def show_community_prob_tree(self, instance):
        if instance:
            render = CommunityIdentificationResult.get_probability_tree(
                individual=instance
            ).get_tree_render()

            return format_html("<textarea readonly>{}</textarea>", render)

    show_community_prob_tree.short_description = _(
        "Community suggestion probability tree"
    )

    def show_computervision_prob_tree(self, instance):
        if instance:
            render = ComputerVisionIdentificationSuggestion.get_probability_tree(
                individual=instance
            ).get_tree_render()

            return format_html("<textarea readonly>{}</textarea>", render)

    show_computervision_prob_tree.short_description = _(
        "Computer vision suggestion probability tree"
    )

    def show_result_prob_tree(self, instance):
        if instance:
            render = EnsembledIdentificationResult.get_probability_tree(
                individual=instance
            ).get_tree_render()

            return format_html("<textarea readonly>{}</textarea>", render)

    show_result_prob_tree.short_description = _("Final probability tree")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs.prefetch_related("photos")
        return qs

    def thumbnail(self, obj):
        if photo := obj.photos.first():
            return format_html(f"<img src='{photo.image.url}' height='75' />")

    thumbnail.allow_tags = True


admin.site.register(Individual, IndividualAdmin)