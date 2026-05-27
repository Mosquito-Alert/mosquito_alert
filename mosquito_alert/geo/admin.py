from django.contrib import admin

from .models import EuropeCountry


@admin.register(EuropeCountry)
class EuropeCountryAdmin(admin.ModelAdmin):
    list_display = ("name_engl", "iso3_code")
    ordering = ["name_engl"]
    search_fields = ["name_engl", "iso3_code"]
