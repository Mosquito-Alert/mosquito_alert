from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from modeltranslation.admin import TranslationAdmin

from .models import Taxon


@admin.register(Taxon)
class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name", "is_relevant")
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon)

    fieldsets = [
        (_("Node position"), {"fields": ("_position", "_ref_node_id")}),
        (
            _("Basic information"),
            {"fields": ("rank", ("name", "is_relevant"), "common_name")},
        ),
    ]
