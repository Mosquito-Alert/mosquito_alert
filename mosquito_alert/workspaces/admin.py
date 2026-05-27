from django.contrib import admin

from .form import WorkspaceAdminForm
from .models import Workspace, WorkspaceMembership, WorkspaceCollaborationGroup


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    form = WorkspaceAdminForm

    list_display = ("id", "__str__", "is_public", "updated_at")
    list_filter = ["country__name_engl", "is_public"]
    ordering = [
        "country__name_engl",
    ]

    readonly_fields = ("updated_at", "country")

    inlines = [WorkspaceMembershipInline]

    def get_fields(self, request, obj=None):
        fields = [
            ("country", "is_public"),
            "geom",
            "supervisor_exclusivity_days",
            "updated_at",
        ]

        if obj and obj.geom:
            fields.insert(1, "name")

        return fields


@admin.register(WorkspaceCollaborationGroup)
class WorkspaceCollaborationGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    ordering = ["name"]
