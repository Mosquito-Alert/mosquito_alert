class TimeStampedModelAdminMixin:
    fields = _timestamp_fields = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    list_display = ("created_at", "updated_at")
    list_filter = ("created_at", "updated_at")

    _timestamp_fieldsets = (
        (
            None,
            {
                "fields": (_timestamp_fields,),
            },
        ),
    )
