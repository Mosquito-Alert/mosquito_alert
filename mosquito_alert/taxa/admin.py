from typing import Any

from django.contrib import admin
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _
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

    fieldsets = [
        (_("Node position"), {"fields": ("_position", "_ref_node_id")}),
        (_("Basic information"), {"fields": ("rank", "name", "gbif_id", "common_name")}),
    ]


@admin.register(SpecieDistribution)
class SpecieDistributionAdmin(SimpleHistoryAdmin):
    list_display = ("boundary", "taxon", "source", "status")
    list_filter = (
        ("taxon", admin.RelatedOnlyFieldListFilter),
        "source",
        "status",
    )
    search_fields = ("boundary__name",)
    ordering = ["taxon", "boundary", "status"]

    history_list_display = ["status", "stats_summary"]

    fields = ("boundary", "taxon", "source", ("status", "status_since"), "pretty_stats_summary")

    autocomplete_fields = ("boundary", "taxon")

    def status(self, obj):
        # Needed to show the displayable value in history view.
        # Not working otherwise...
        return obj.get_status_display()

    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        readonly_fields = ["pretty_stats_summary", "status_since"]

        if obj:
            readonly_fields += ["boundary", "taxon", "source"]
            if obj.source == SpecieDistribution.DataSource.SELF:
                # Not allowing editing status since it is auto computed.
                readonly_fields += ["status"]

        return tuple(readonly_fields)
