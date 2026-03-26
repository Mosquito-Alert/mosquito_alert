from django.db import models

from mosquito_alert.geo.models import EuropeCountry


class OWCampaigns(models.Model):
    """
    This model contains the information about Overwintering campaigns. Each campaign takes place in a given country,
    over a period of time. In a given country at a given period, only one campaign can be active.
    """

    country = models.ForeignKey(
        EuropeCountry,
        related_name="campaigns",
        help_text="Country in which the campaign is taking place",
        on_delete=models.PROTECT,
    )
    posting_address = models.TextField(
        help_text="Full posting address of the place where the samples will be sent"
    )
    campaign_start_date = models.DateTimeField(
        help_text="Date when the campaign starts. No samples should be collected BEFORE this date."
    )
    campaign_end_date = models.DateTimeField(
        help_text="Date when the campaign ends. No samples should be collected AFTER this date."
    )

    class Meta:
        db_table = "tigaserver_app_owcampaigns"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
