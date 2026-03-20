from django.db import models

class RankingData(models.Model):
    user_uuid = models.CharField(max_length=36, primary_key=True, help_text='User identifier uuid')
    class_value = models.CharField(max_length=60)
    rank = models.IntegerField()
    score_v2 = models.IntegerField()
    last_update = models.DateTimeField(help_text="Last time ranking data was updated", null=True, blank=True)

    class Meta:
        db_table = 'tigaserver_app_rankingdata' # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.