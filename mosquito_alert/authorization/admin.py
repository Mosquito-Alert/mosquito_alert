from django.contrib import admin

from .models import BoundaryAuthorization, BoundaryMembership


class BoundaryMembershipInline(admin.StackedInline):
    model = BoundaryMembership
    extra = 1
    fields = ("user", "role")


@admin.register(BoundaryAuthorization)
class BoundaryAuthorizationAdmin(admin.ModelAdmin):
    list_display = ("boundary", "supervisor_exclusivity_days", "members_only")
    search_fields = ("boundary__name",)

    fields = ("boundary", "supervisor_exclusivity_days", "members_only")
    inlines = [BoundaryMembershipInline]
