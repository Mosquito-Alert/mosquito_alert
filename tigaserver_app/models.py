from django.db import models
import uuid
import os
import datetime
from django.utils.timezone import utc


class TigaUser(models.Model):
    user_UUID = models.CharField(max_length=36, primary_key=True)

    def __unicode__(self):
        return self.user_UUID


class Mission(models.Model):
    mission_id = models.CharField(max_length=200, primary_key=True)
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
    version_UUID = models.CharField(max_length=36, primary_key=True)
    version_number = models.IntegerField()
    user = models.ForeignKey(TigaUser)
    report_id = models.CharField(max_length=200)
    server_upload_time = models.DateTimeField(auto_now_add=True)
    phone_upload_time = models.BigIntegerField()
    creation_time = models.BigIntegerField()
    version_time = models.BigIntegerField()
    type = models.IntegerField()
    mission = models.ForeignKey(Mission, blank=True, null=True)
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
        unique_together = ("user", "version_UUID")


def get_unique_image_file_path(filename='default.jpg'):
    extension = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), extension)
    root = 'tigapics'
    return os.path.join(root, filename)


class Photo(models.Model):
    photo = models.ImageField(upload_to="tigapics")
    report = models.ForeignKey(Report)

    def __unicode__(self):
        return self.photo.name


class Fix(models.Model):
    user = models.ForeignKey(TigaUser)
    time = models.BigIntegerField()