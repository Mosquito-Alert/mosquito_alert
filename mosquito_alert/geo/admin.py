from django.contrib import admin

from .models import Country, Subregion


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name_engl", "iso2_code", "iso3_code", "wikidata_id")
    ordering = ["name_engl"]
    search_fields = ["name_engl", "iso2_code", "iso3_code", "wikidata_id"]


class CountryAdminInline(admin.TabularInline):
    model = Country
    extra = 0
    fields = ("name_engl", "iso2_code", "iso3_code", "wikidata_id")
    readonly_fields = ("name_engl", "iso2_code", "iso3_code", "wikidata_id")
    can_delete = False
    show_change_link = True


@admin.register(Subregion)
class SubregionAdmin(admin.ModelAdmin):
    list_display = ("name", "continent")
    ordering = ["continent", "name"]
    search_fields = ["name", "continent"]

    inlines = [CountryAdminInline]
