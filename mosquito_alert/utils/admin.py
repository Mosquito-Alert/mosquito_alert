from flag.models import Flag, FlagInstance
from nested_admin.nested import NestedGenericTabularInline, NestedTabularInline


class FlagInstanceInlineAdmin(NestedTabularInline):
    model = FlagInstance
    is_sortable = False
    extra = 0


class FlaggedContentInlineAdmin(NestedGenericTabularInline):
    model = Flag
    inlines = [FlagInstanceInlineAdmin]
    classes = ["collapse"]
    extra = 0
    max_num = 1
    is_sortable = False
    readonly_fields = [
        "count",
    ]
