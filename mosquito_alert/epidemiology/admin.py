from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import Disease, DiseaseVector


class DiseaseVectorsInlineAdmin(admin.TabularInline):
    model = DiseaseVector.diseases.through
    extra = 0


class DiseasesAdmin(TranslationAdmin):
    inlines = [
        DiseaseVectorsInlineAdmin,
    ]


class DiseaseVectorsAdmin(admin.ModelAdmin):
    autocomplete_fields = ("taxon",)
    search_fields = ("taxon",)
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


admin.site.register(Disease, DiseasesAdmin)
admin.site.register(DiseaseVector, DiseaseVectorsAdmin)
