from __future__ import unicode_literals
from django.db import models
# from django.db.models.functions import Concat
# from django.db.models import CharField, Value as V

class MapAuxReports(models.Model):
    id = models.IntegerField(primary_key=True)
    version_uuid = models.CharField(max_length=36, blank=True)
    observation_date = models.DateTimeField(null=True, blank=True)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    ref_system = models.CharField(max_length=36, blank=True)
    type = models.CharField(max_length=7, blank=True)

    # breeding_site_answers = models.CharField(max_length=100, blank=True)
    # mosquito_answers = models.CharField(max_length=100, blank=True)

    t_q_1 = models.CharField(max_length=255, blank=True)
    t_a_1 = models.CharField(max_length=255, blank=True)
    t_q_2 = models.CharField(max_length=255, blank=True)
    t_a_2 = models.CharField(max_length=255, blank=True)
    t_q_3 = models.CharField(max_length=255, blank=True)
    t_a_3 = models.CharField(max_length=255, blank=True)

    s_q_1 = models.CharField(max_length=255, blank=True)
    s_a_1 = models.CharField(max_length=255, blank=True)
    s_q_2 = models.CharField(max_length=255, blank=True)
    s_a_2 = models.CharField(max_length=255, blank=True)
    s_q_3 = models.CharField(max_length=255, blank=True)
    s_a_3 = models.CharField(max_length=255, blank=True)
    s_q_4 = models.CharField(max_length=255, blank=True)
    s_a_4 = models.CharField(max_length=255, blank=True)

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
    private_webmap_layer = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = 'map_aux_reports'
        #test = type
