from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from ..utils.forms import ParentManageableMoveNodeForm
from .models import Taxon


class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name")
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon, form=ParentManageableMoveNodeForm)


admin.site.register(Taxon, TaxonAdmin)
