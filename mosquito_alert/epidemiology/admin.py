from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from mosquito_alert.taxa.admin import MonthlyDistributionAdmin

from .models import Disease, DiseaseVector
from .models import MonthlyDistribution as VectorMonthlyDistribution


class DiseaseVectorsInlineAdmin(admin.TabularInline):
    model = DiseaseVector.diseases.through
    extra = 0


class DiseasesAdmin(TranslationAdmin):
    inlines = [
        DiseaseVectorsInlineAdmin,
    ]


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


class VectorMonthlyDistributionAdmin(MonthlyDistributionAdmin):
    def has_add_permission(self, request) -> bool:
        return False


admin.site.register(Disease, DiseasesAdmin)
admin.site.register(DiseaseVector, DiseaseVectorsAdmin)
admin.site.register(VectorMonthlyDistribution, VectorMonthlyDistributionAdmin)
