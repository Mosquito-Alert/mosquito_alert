import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer

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

    preview.allow_tags = True


class PhotoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "user", "created_at", "preview")
    list_filter = ("user", "created_at")
    fields = ("created_at", ("image", "preview"))
    readonly_fields = ("preview", "created_at")
    list_per_page = 10

    def preview(self, obj):
        if obj.pk:
            return format_html(f"<img src='{obj.image.url}' height='150' />")
        return "Upload image for preview"

    preview.allow_tags = True

    def exif_dict(self, obj):
        response = json.dumps(dict(obj.exif_dict), sort_keys=True, indent=2)
        # Get the Pygments formatter
        formatter = HtmlFormatter(style="colorful")
        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)
        # Get the stylesheet
        style = "<style>" + formatter.get_style_defs() + "</style><br>"
        # Safe the output
        return mark_safe(style + response)

    exif_dict.short_description = "EXIF"

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Only set added_by during the first save.
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        result = self.fields
        if obj:
            result += ("user",)

        if obj and request.user.has_perm(perm="view_exif", obj=obj):
            result += ("exif_dict",)

        return result

    def get_readonly_fields(self, request, obj=None):
        result = self.readonly_fields

        if obj:
            result += ("user",)

        if obj and request.user.has_perm(perm="view_exif", obj=obj):
            result += ("exif_dict",)
        return result


admin.site.register(Photo, PhotoAdmin)
