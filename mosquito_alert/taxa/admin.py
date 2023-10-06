from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from simple_history.admin import SimpleHistoryAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from ..utils.forms import ParentManageableMoveNodeForm
from .models import SpecieDistribution, Taxon


@admin.register(Taxon)
class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name")
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon, form=ParentManageableMoveNodeForm)

    group_fieldsets = True


@admin.register(SpecieDistribution)
class SpecieDistributionAdmin(SimpleHistoryAdmin):
    list_display = ("boundary", "taxon", "source", "status")
    history_list_display = ["status"]
    list_filter = (
        ("boundary", admin.RelatedOnlyFieldListFilter),
        ("taxon", admin.RelatedOnlyFieldListFilter),
        "source",
        "status",
    )

    def status(self, obj):
        # Needed to show the displayable value.
        # Not working otherwise...
        return obj.get_status_display()


class SpecieDistributionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "history_date",
        "history_type",
        "status",
    )
    search_fields = ("id",)
    list_filter = (
        "history_date",
        "history_type",
        "status",
    )

    def has_add_permission(self, request) -> bool:
        return False


admin.site.register(SpecieDistribution.history.model, SpecieDistributionHistoryAdmin)
