
from django.contrib.gis.db import models


class OrganizationPin(models.Model):
    """
    This model is queryable via API, it's meant to represent a list of organizations with a geographical location.
    Each of these organizations has a link to a web page with the detailed information. The text in textual_description
    should be shown in a pin dialog in a map
    """
    point = models.PointField(srid=4326)
    textual_description = models.TextField(help_text='Text desription on the pin. This text is meant to be visualized as the text body of the dialog on the map')
    page_url = models.URLField(help_text='URL link to the organization page')

    class Meta:
        db_table = "tigaserver_app_organizationpin"  # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
