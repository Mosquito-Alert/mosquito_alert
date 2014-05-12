from django.db import models


class TigaUser(models.Model):
    user_id = models.CharField(max_length=200, primary_key=True)

    def __unicode__(self):
        return self.user_id


class Report(models.Model):
    user = models.ForeignKey(TigaUser)
    report_id = models.CharField(max_length=200)
    version = models.IntegerField()
    server_upload_time = models.DateTimeField(auto_now_add=True)
    phone_upload_time = models.BigIntegerField()
    creation_time = models.BigIntegerField()
    version_time = models.BigIntegerField()
    type = models.IntegerField()
    mission_id = models.ForeignKey(Mission)
    confirmation = models.CharField(max_length=1000)
    confirmation_code = models.IntegerField()
    location_choice = models.IntegerField()
    current_location_lon = models.FloatField()
    current_location_lat = models.FloatField()
    selected_location_lon = models.FloatField()
    selected_location_lat = models.FloatField()
    photo_attached = models.BooleanField()
    photo = models.ImageField()
    note = models.CharField(max_length=1000)
    package_name = models.CharField(max_length=400)
    package_version = models.IntegerField()
    phone_manufacturer = models.CharField(max_length=200)
    phone_model = models.CharField(max_length=200)
    os = models.CharField(max_length=200)
    os_version = models.CharField(max_length=200)

    def __unicode__(self):
        return self.report_id


class Mission(models.Model):
    mission_id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=200)
    creation_time = models.BigIntegerField()
    expiration_time = models.BigIntegerField()
    mission_detail = models.CharField(max_length=1000)


class MissionLocationTriggers(models.Model):
    mission_id = models.ForeignKey(Mission)
    lat = models.FloatField()
    lon = models.FloatField()


class MissionTimeTriggers(models.Model):
    mission_id = models.ForeignKey(Mission)
    lower_bound = models.BigIntegerField()
    upper_bound = models.BigIntegerField()

