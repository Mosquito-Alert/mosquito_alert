from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField
from django.http.request import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from mosquito_alert.utils.admin import TimeStampedModelAdminMixin


class BaseAnnotatorProfileAdminMixin(TimeStampedModelAdminMixin):
    _annotator_profile_fields = ("user", "is_active")

    fields = None
    readonly_fields = TimeStampedModelAdminMixin.readonly_fields
    fieldsets = (
        (
            _("Profile information"),
            {
                "fields": _annotator_profile_fields,
            },
        ),
    ) + TimeStampedModelAdminMixin._timestamp_fieldsets
    autocomplete_fields = ("user",)

    search_fields = ("user__username", "user__name")

    list_display = _annotator_profile_fields + TimeStampedModelAdminMixin.list_display
    list_filter = ("is_active",) + TimeStampedModelAdminMixin.list_filter

    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        result = TimeStampedModelAdminMixin.readonly_fields
        if obj:
            result += ("user",)

        return result


class BaseTaskAdminMixin(TimeStampedModelAdminMixin):
    _task_fields = ("is_completed",)

    fields = _task_fields + TimeStampedModelAdminMixin._timestamp_fields
    readonly_fields = TimeStampedModelAdminMixin.readonly_fields

    list_display = _task_fields + TimeStampedModelAdminMixin.list_display
    list_filter = _task_fields + TimeStampedModelAdminMixin.list_filter


class BaseAnnotationTaskAdminMixin(BaseTaskAdminMixin):
    _annotation_task_fields = ("skipped_annotations", "total_annotations", "total_predictions")

    fields = _annotation_task_fields + BaseTaskAdminMixin.fields
    readonly_fields = _annotation_task_fields + BaseTaskAdminMixin.readonly_fields

    list_display = _annotation_task_fields + TimeStampedModelAdminMixin.list_display
    list_filter = _annotation_task_fields + TimeStampedModelAdminMixin.list_filter


class BasePhotoAnnotationTaskAdminMixin(BaseAnnotationTaskAdminMixin):
    _photo_annotation_task_fields = ("photo",)

    fields = BaseAnnotationTaskAdminMixin.fields + _photo_annotation_task_fields
    readonly_fields = ("preview",) + BaseAnnotationTaskAdminMixin.readonly_fields

    search_fields = ("photo__image",)
    list_display = _photo_annotation_task_fields + TimeStampedModelAdminMixin.list_display
    list_filter = TimeStampedModelAdminMixin.list_filter

    @admin.display(description=_("Photo preview"))
    def preview(self, obj):
        if obj.pk:
            return format_html(f"<img src='{obj.photo.image.url}' height='150' />")
        return "Upload image for preview"


class BaseAnnotationAdminMixin:
    fields = _annotation_fields = ("label",)
    autocomplete_fields = _annotation_fields

    list_display = _annotation_fields
    list_filter = ("label",)


class BasePhotoAnnotationAdminMixin(BaseAnnotationAdminMixin):
    _photo_annotation_fields = ("task",)

    fields = _photo_annotation_fields + BaseAnnotationAdminMixin.fields


class BaseShapeAdminMixin:
    fields = _shape_fields = ("shape_type", "points")

    class ShapeForm(forms.ModelForm):
        points = SimpleArrayField(SimpleArrayField(forms.FloatField(max_value=1, min_value=0)), delimiter="|")

    form = ShapeForm

    _shape_fieldsets = (
        (
            _("Localization"),
            {
                "fields": (("shape_type", "points"),),
            },
        ),
    )
