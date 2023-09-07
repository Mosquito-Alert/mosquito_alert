from django.contrib import admin
from django.http.request import HttpRequest
from django.utils.html import format_html
from nested_admin.nested import NestedModelAdmin

from mosquito_alert.identifications.admin import IndividualIdentificationTaskAdminInline

from .models import Individual


@admin.register(Individual)
class IndividualAdmin(NestedModelAdmin):
    list_display = ["__str__", "is_identified", "thumbnail"]

    fields = ("taxon", "is_identified")
    readonly_fields = ("taxon", "is_identified")

    inlines = [IndividualIdentificationTaskAdminInline]

    def thumbnail(self, obj):
        if photo := obj.photos.first():
            return format_html(f"<img src='{photo.image.url}' height='75' />")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
