from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from mosquito_alert.taxa.admin import SpecieDistributionAdmin

from .models import Disease, DiseaseVector, DiseaseVectorDistribution


class DiseaseVectorsInlineAdmin(admin.TabularInline):
    model = DiseaseVector.diseases.through
    extra = 0


@admin.register(Disease)
class DiseasesAdmin(TranslationAdmin):
    inlines = [
        DiseaseVectorsInlineAdmin,
    ]


@admin.register(DiseaseVector)
class DiseaseVectorsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("taxon",)
    search_fields = ("taxon__name",)
    filter_horizontal = ("diseases",)
    list_display = ("taxon", "get_diseases")
    list_filter = (
        ("taxon", admin.RelatedOnlyFieldListFilter),
        ("diseases", admin.RelatedOnlyFieldListFilter),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("diseases")

    @admin.display(description="Diseases")
    def get_diseases(self, obj):
        return ", ".join([d.name for d in obj.diseases.all()])


@admin.register(DiseaseVectorDistribution)
class DiseaseVectorDistributionAdmin(SpecieDistributionAdmin):
    def has_add_permission(self, request) -> bool:
        return False
