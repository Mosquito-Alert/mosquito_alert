from __future__ import unicode_literals
from django.db import models


class MapAuxReports(models.Model):
    id = models.IntegerField(primary_key=True)
    version_uuid = models.CharField(max_length=36, blank=True)
    observation_date = models.DateTimeField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    ref_system = models.CharField(max_length=36, blank=True)
    type = models.CharField(max_length=7, blank=True)
    breeding_site_answers = models.CharField(max_length=100, blank=True)
    mosquito_answers = models.CharField(max_length=100, blank=True)
    expert_validated = models.NullBooleanField()
    expert_validation_result = models.CharField(max_length=100, blank=True)
    simplified_expert_validation_result = models.CharField(max_length=100,
                                                           blank=True)
    site_cat = models.IntegerField(blank=True, null=True)
    storm_drain_status = models.CharField(max_length=50, blank=True)
    edited_user_notes = models.CharField(max_length=4000, blank=True)
    photo_url = models.CharField(max_length=255, blank=True)
    photo_license = models.CharField(max_length=100, blank=True)
    dataset_license = models.CharField(max_length=100, blank=True)
    single_report_map_url = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = 'map_aux_reports'
