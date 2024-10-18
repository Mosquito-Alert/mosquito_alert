import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from imagekit.admin import AdminThumbnail
from nested_admin.nested import NestedModelAdmin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

from mosquito_alert.identifications.admin import PhotoIdentificationTaskAdminInline
from mosquito_alert.moderation.admin import FlaggedContentNestedInlineAdmin

from .models import Photo


class m2mPhotoAdminInlineMixin:
    extra = 0
    can_delete = False
    fields = [
        "photo",
        "image_thumbnail",
    ]
    readonly_fields = [
        "image_thumbnail",
    ]

    image_thumbnail = AdminThumbnail(image_field=lambda obj: obj.photo.thumbnail)


@admin.register(Photo)
class PhotoAdmin(NestedModelAdmin):
    list_display = ("__str__", "user", "created_at", "image_thumbnail")
    list_filter = ("user", "created_at")
    fields = ("created_at", ("image", "image_thumbnail"))
    readonly_fields = ("image_thumbnail", "created_at")
    list_per_page = 10

    image_thumbnail = AdminThumbnail(image_field="thumbnail")

    inlines = [FlaggedContentNestedInlineAdmin, PhotoIdentificationTaskAdminInline]

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
        if obj._state.adding:
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
