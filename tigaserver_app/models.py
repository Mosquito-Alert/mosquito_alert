from django.db import models
import datetime
from django.utils.timezone import utc


class TigaUser(models.Model):
    user_UUID = models.CharField(max_length=36, primary_key=True)

    def __unicode__(self):
        return self.user_UUID


class Mission(models.Model):
    mission_id = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=200)
    creation_time = models.DateTimeField()
    expiration_time = models.DateTimeField(blank=True, null=True)
    mission_detail = models.CharField(max_length=1000)
    location_trigger_lat = models.FloatField(blank=True, null=True)
    location_trigger_lon = models.FloatField(blank=True, null=True)
    time_trigger_lower_bound = models.TimeField(blank=True, null=True)
    time_trigger_upper_bound = models.TimeField(blank=True, null=True)

    def __unicode__(self):
        return self.mission_id

    def active_missions(self):
        return self.expiration_time >= datetime.datetime.utcnow().replace(tzinfo=utc)


class Report(models.Model):
    user = models.ForeignKey(TigaUser)
    report_id = models.CharField(max_length=200)
    version_UUID = models.CharField(max_length=36, primary_key=True)
    version_number = models.IntegerField()
    server_upload_time = models.DateTimeField(auto_now_add=True)
    phone_upload_time = models.BigIntegerField()
    creation_time = models.BigIntegerField()
    version_time = models.BigIntegerField()
    type = models.IntegerField()
    mission_id = models.ForeignKey(Mission, blank=True, null=True)
    confirmation = models.CharField(max_length=1000)
    confirmation_code = models.IntegerField(blank=True, null=True)
    location_choice = models.IntegerField()
    current_location_lon = models.FloatField(blank=True, null=True)
    current_location_lat = models.FloatField(blank=True, null=True)
    selected_location_lon = models.FloatField(blank=True, null=True)
    selected_location_lat = models.FloatField(blank=True, null=True)
    note = models.CharField(max_length=1000, blank=True)
    package_name = models.CharField(max_length=400, blank=True)
    package_version = models.IntegerField(blank=True, null=True)
    phone_manufacturer = models.CharField(max_length=200, blank=True)
    phone_model = models.CharField(max_length=200, blank=True)
    os = models.CharField(max_length=200, blank=True)
    os_version = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.version_UUID

    class Meta:
        unique_together = ("user", "report_id")


class Photo(models.Model):
    photo = models.ImageField(upload_to='tigapics')
