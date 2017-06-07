from __future__ import unicode_literals
from django.conf import settings
from datetime import datetime
from django.db import models

#from django.contrib.gis.db import models
#from django.contrib.gis.gdal import DataSource

#from django.contrib.gis.utils import LayerMapping
#from django.contrib.auth.models import User, Group

# from django.db.models.functions import Concat
# from django.db.models import CharField, Value as V

class NotificationImageFormModel(models.Model):
    image = models.ImageField(upload_to=settings.MEDIA_ROOT)
    class Meta:
        db_table = None

class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField()
    is_superuser = models.BooleanField()
    username = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'auth_user'

class MapAuxReports(models.Model):
    id = models.IntegerField(primary_key=True)
    version_uuid = models.CharField(max_length=36, blank=True, unique=True)
    user_id = models.CharField(max_length=36, blank=True)
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
    final_expert_status = models.IntegerField()
    note = models.TextField()

    class Meta:
        managed = False
        db_table = 'map_aux_reports'
        #test = type

class StormDrain(models.Model):
    id = models.AutoField(primary_key=True)
    icon = models.IntegerField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    municipality = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=100, blank=True)
    water = models.BooleanField(max_length=10, blank=True)
    sand = models.BooleanField(max_length=10, blank=True)
    treatment = models.BooleanField(max_length=10, blank=True)
    species2 = models.BooleanField(max_length=10, blank=True)
    species1 = models.BooleanField(max_length=10, blank=True)
    activity = models.BooleanField(max_length=10, blank=True)
    code = models.CharField(max_length=50, blank=True)
    lon = models.DecimalField(max_digits=15,decimal_places=6)
    lat = models.DecimalField(max_digits=15,decimal_places=6)
    user = models.ForeignKey(AuthUser)
    date = models.DateTimeField(default=datetime.now(), blank=True)
    original_lon = models.FloatField(blank=True, null=True)
    original_lat = models.FloatField(blank=True, null=True)
    idalfa = models.CharField(max_length=5, blank=True)
    size = models.CharField(max_length=5, blank=True)
    model = models.CharField(max_length=5, blank=True)

    class Meta:
        #managed = False
        db_table = 'storm_drain'

class NotificationContent(models.Model):
    id = models.AutoField(primary_key=True, help_text='Unique identifier of the notification. Automatically generated by ' \
                                                  'server when notification created.')
    body_html_es = models.TextField(help_text='Expert comment, expanded and allows html, in spanish')
    body_html_ca = models.TextField(default=None,blank=True,null=True,help_text='Expert comment, expanded and allows html, in catalan')
    body_html_en = models.TextField(default=None,blank=True,null=True,help_text='Expert comment, expanded and allows html, in english')
    title_es = models.TextField(help_text='Title of the comment, shown in non-detail view, in spanish')
    title_ca = models.TextField(default=None,blank=True,null=True,help_text='Title of the comment, shown in non-detail view, in catalan')
    title_en = models.TextField(default=None,blank=True,null=True,help_text='Title of the comment, shown in non-detail view, in english')

    class Meta:
        managed = False
        db_table = 'tigaserver_app_notificationcontent'

class Notification(models.Model):
    #report_id = models.CharField(max_length=36, blank=False)
    report = models.ForeignKey(MapAuxReports, to_field='version_uuid')
    user_id = models.CharField(max_length=36, blank=False)
    expert = models.ForeignKey(AuthUser)
    date_comment = models.DateTimeField(default=datetime.now())
    expert_comment = models.TextField('Expert comment', help_text='Text message sent to user')
    expert_html = models.TextField('Expert comment, expanded and allows html', help_text='Expanded message information goes here. This field can contain HTML')
    photo_url = models.TextField('Url to picture that originated the comment', null=True, blank=True, help_text='Relative url to the public report photo')
    acknowledged = models.BooleanField(default=False,help_text='This is set to True through the public API, when the user signals that the message has been received')
    public = models.BooleanField(default=False)
    notification_content = models.ForeignKey(NotificationContent)

    class Meta:
        managed = False
        db_table = 'tigaserver_app_notification'


# class StormDrainRepresentation(models.Model):
#     id = models.AutoField(primary_key=True)
#     user = models.ForeignKey(AuthUser)
#     version = models.IntegerField()
#     condition = models.IntegerField()
#     key = models.CharField(max_length=36, blank=False)
#     value = models.CharField(max_length=36, blank=False)
#     operator = models.CharField(max_length=15, blank=False)
#
#     class Meta:
#         #managed = False
#         db_table = 'tigapublic_storm_drain_representation'

class StormDrainUserVersions(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AuthUser)
    version = models.IntegerField()
    published_date = models.DateTimeField(default=datetime.now())
    style_json = models.TextField()
    visible = models.BooleanField()
    title = models.CharField(max_length=50, blank=True)

    class Meta:
        #managed = False
        db_table = 'tigapublic_storm_drain_user_version'
