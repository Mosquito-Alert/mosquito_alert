
from django.contrib import admin

from .models import OWCampaigns

@admin.register(OWCampaigns)
class OWCampaignsAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'posting_address', 'campaign_start_date', 'campaign_end_date')
    list_filter = ['country__name_engl', 'posting_address']
    ordering = ['country', 'campaign_start_date', 'campaign_end_date']
