from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import OrganizationPin

@admin.register(OrganizationPin)
class OrganizationPinAdmin(GISModelAdmin):
    list_display = ('id', 'point', 'textual_description', 'page_url')
    list_filter = ['textual_description', 'page_url']
    search_fields = ['textual_description', 'page_url']
