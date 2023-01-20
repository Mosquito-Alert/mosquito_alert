from django.contrib import admin
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
    fields = ["first_observed_at"]
    readonly_fields = ["first_observed_at"]
    list_filter = ["identification_set__taxon"]
    inlines = [ReadOnlyPhotoAdminInline, IdentificationSetAdminInline]


admin.site.register(Individual, IndividualAdmin)
