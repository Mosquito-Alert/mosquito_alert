from django.contrib import admin
from django.utils.html import format_html
from nested_admin.nested import (
    NestedModelAdmin,
    NestedStackedInline,
    NestedTabularInline,
)

from mosquito_alert.images.admin import m2mPhotoAdminInlineMixin

from .models import Identification, IdentificationSet, Individual


class ReadOnlyPhotoAdminInline(m2mPhotoAdminInlineMixin, NestedTabularInline):
    model = Individual.photos.through
    is_sortable = False


class IdentificationAdminInline(NestedStackedInline):
    model = Identification
    is_sortable = False
    extra = 0


class IdentificationSetAdminInline(NestedStackedInline):
    model = IdentificationSet
    inlines = [IdentificationAdminInline]
    max_num = 0
    is_sortable = False
    readonly_fields = ["agreement"]


class IndividualAdmin(NestedModelAdmin):
    fields = ["first_observed_at", "is_identified"]
    readonly_fields = ["first_observed_at", "is_identified"]
    list_display = ["__str__", "is_identified", "thumbnail"]
    list_filter = [
        "is_identified",
        ("identification_set__taxon", admin.RelatedOnlyFieldListFilter),
    ]
    inlines = [ReadOnlyPhotoAdminInline, IdentificationSetAdminInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs.prefetch_related("photos").select_related("identification_set")
        return qs

    def thumbnail(self, obj):
        if photo := obj.photos.first():
            return format_html(f"<img src='{photo.image.url}' height='75' />")

    thumbnail.allow_tags = True


admin.site.register(Individual, IndividualAdmin)
