from django.contrib import admin

from .models import Workspace, WorkspaceMembership, WorkspaceCollaborationGroup


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("id", "country", "is_public", "updated_at")
    list_filter = ["country__name_engl"]
    ordering = [
        "country__name_engl",
    ]

    inlines = [WorkspaceMembershipInline]


@admin.register(WorkspaceCollaborationGroup)
class WorkspaceCollaborationGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    ordering = ["name"]
