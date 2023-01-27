from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from ..utils.forms import ParentManageableMoveNodeForm
from .models import MonthlyDistribution, Taxon


class TaxonAdmin(TreeAdmin, TranslationAdmin):
    search_fields = ("name",)
    list_display = ("name", "rank", "common_name")
    list_filter = ("rank",)

    # For TreeAdmin
    form = movenodeform_factory(Taxon, form=ParentManageableMoveNodeForm)


class MonthlyDistributionAdmin(admin.ModelAdmin):
    list_display = ("boundary", "month", "taxon", "status")
    list_filter = (
        ("boundary", admin.RelatedOnlyFieldListFilter),
        "month",
        ("taxon", admin.RelatedOnlyFieldListFilter),
        "status",
    )


admin.site.register(Taxon, TaxonAdmin)
admin.site.register(MonthlyDistribution, MonthlyDistributionAdmin)
