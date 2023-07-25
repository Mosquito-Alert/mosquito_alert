from django.contrib.admin.options import InlineModelAdmin
from django.contrib.contenttypes.admin import GenericInlineModelAdmin
from flag.models import Flag, FlagInstance
from nested_admin.nested import NestedGenericTabularInlineMixin, NestedTabularInlineMixin


class FlagInstanceInlineAdmin(InlineModelAdmin):
    model = FlagInstance
    extra = 0


class FlagInstanceNestedInlineAdmin(NestedTabularInlineMixin, FlagInstanceInlineAdmin):
    is_sortable = False


class FlaggedContentInlineAdmin(GenericInlineModelAdmin):
    model = Flag
    inlines = [FlagInstanceInlineAdmin]
    classes = ["collapse"]
    extra = 0
    max_num = 1

    readonly_fields = [
        "count",
    ]


class FlaggedContentNestedInlineAdmin(NestedGenericTabularInlineMixin, FlaggedContentInlineAdmin):
    is_sortable = False
