import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from nested_admin.polymorphic import NestedPolymorphicModelAdmin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

from mosquito_alert.identifications.admin import ImageTaxonPredictionRunAdminInline
from mosquito_alert.utils.admin import FlaggedContentInlineAdmin

from .models import Photo


class m2mPhotoAdminInlineMixin:
    extra = 0
    can_delete = False
    fields = [
        "photo",
        "preview",
    ]
    readonly_fields = [
        "preview",
    ]

    def preview(self, obj):
        if obj.pk:
            return format_html(f"<img src='{obj.photo.image.url}' height='150' />")
        return "Upload image for preview"


@admin.register(Photo)
class PhotoAdmin(NestedPolymorphicModelAdmin):
    list_display = ("__str__", "user", "created_at", "preview")
    list_filter = ("user", "created_at")
    fields = ("created_at", ("image", "preview"))
    readonly_fields = ("preview", "created_at")
    list_per_page = 10

    inlines = [FlaggedContentInlineAdmin, ImageTaxonPredictionRunAdminInline]

    def preview(self, obj):
        if obj.pk:
            return format_html(f"<img src='{obj.image.url}' height='150' />")
        return "Upload image for preview"

    @admin.display(description="EXIF")
    def exif_dict(self, obj):
        response = json.dumps(dict(obj.exif_dict), sort_keys=True, indent=2)
        # Get the Pygments formatter
        formatter = HtmlFormatter(style="colorful")
        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)
        # Safe the output
        return format_html("<style>{}</style><br>{}", formatter.get_style_defs(), mark_safe(response))  # nosec

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Only set added_by during the first save.
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        result = self.fields
        if obj:
            result += ("user",)
            if request.user.has_perm(perm=f"{obj._meta.app_label}.view_exif"):
                result += ("exif_dict",)

        return result

    def get_readonly_fields(self, request, obj=None):
        result = self.readonly_fields

        if obj:
            result += ("user",)
            if request.user.has_perm(perm=f"{obj._meta.app_label}.view_exif"):
                result += ("exif_dict",)
        return result
