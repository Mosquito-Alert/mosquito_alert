from rest_framework import serializers

from mosquito_alert.campaigns.models import OWCampaigns


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = OWCampaigns
        fields = ("id", "country_id", "posting_address", "start_date", "end_date")
        extra_kwargs = {
            "start_date": {"source": "campaign_start_date"},
            "end_date": {"source": "campaign_end_date"},
        }
