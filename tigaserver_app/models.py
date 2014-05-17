from django.db import models
import uuid
import os
import datetime
from django.utils.timezone import utc


class TigaUser(models.Model):
    user_UUID = models.CharField(max_length=36, primary_key=True, help_text='UUID randomly generated on '
                                                'phone to identify each unique user. Must be exactly 36 '
                                                'characters (32 hex digits plus 4 hyphens).')
    consent_time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.user_UUID

    def number_of_fixes_uploaded(self):
        return Fix.objects.filter(user=self).count()

    def number_of_reports_uploaded(self):
        return Report.objects.filter(user=self).count()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class Mission(models.Model):
    title = models.CharField(max_length=200, help_text='Title of mission')
    short_description = models.CharField(max_length=200, help_text='Text to be displayed in mission list.')
    long_description = models.CharField(max_length=1000, help_text='Text that fully explains mission to user')
    help_text = models.TextField(blank=True, help_text='Text to be displayed when user taps mission help button.')
    LANGUAGE_CHOICES = (('ca', 'Catalan'), ('es', 'Spanish'), ('en', 'English'), )
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES,  help_text='What language is mission '
                                                                                   'displayed in? (It will be sent '
                                                                                   'only users who have chosen this '
                                                                                   'language')
    PLATFORM_CHOICES = (('and', 'Android'), ('ios', 'iOS'), ('html', 'HTML5'), ('all', 'All platforms'),)
    platform = models.CharField(max_length=4, choices=PLATFORM_CHOICES, help_text='What type of device is this '
                                                                                   'mission is intended for? It will '
                                                                                   'be sent only to these devices')
    creation_time = models.DateTimeField(auto_now=True)
    expiration_time = models.DateTimeField(blank=True, null=True)
    location_trigger_lat = models.FloatField(blank=True, null=True)
    location_trigger_lon = models.FloatField(blank=True, null=True)
    time_trigger_lower_bound = models.TimeField(blank=True, null=True)
    time_trigger_upper_bound = models.TimeField(blank=True, null=True)
    button_left_visible = models.BooleanField()
    button_middle_visible = models.BooleanField()
    button_right_visible = models.BooleanField()
    button_left_text = models.CharField(max_length=100, blank=True)
    button_left_action = models.IntegerField(blank=True, null=True)
    button_left_url = models.URLField(blank=True, null=True)
    button_middle_text = models.CharField(max_length=100, blank=True)
    button_middle_action = models.IntegerField(blank=True, null=True)
    button_middle_url = models.URLField(blank=True, null=True)
    button_right_text = models.CharField(max_length=100, blank=True)
    button_right_action = models.IntegerField(blank=True, null=True)
    button_right_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.title

    def active_missions(self):
        return self.expiration_time >= datetime.datetime.utcnow().replace(tzinfo=utc)


class MissionItem(models.Model):
    mission = models.ForeignKey(Mission, related_name='items')
    question = models.CharField(max_length=1000, help_text='Question to be displayed to user.')
    answer_choices = models.CharField(max_length=1000, help_text='Response choices. Please separate them with commas.')
    help_text = models.TextField(blank=True)
    prepositioned_image_reference = models.IntegerField(blank=True, null=True)
    attached_image = models.ImageField(upload_to='tigaserver_mission_images', blank=True, null=True)


class Report(models.Model):
    version_UUID = models.CharField(max_length=36, primary_key=True, help_text='UUID randomly generated on '
                                                'phone to identify each unique report version. Must be exactly 36 '
                                                'characters (32 hex).')
    version_number = models.IntegerField()
    user = models.ForeignKey(TigaUser)
    report_id = models.CharField(max_length=200)
    server_upload_time = models.DateTimeField(auto_now_add=True)
    phone_upload_time = models.DateTimeField()
    creation_time = models.DateTimeField()
    version_time = models.DateTimeField()
    TYPE_CHOICES = (('adult', 'Adult'), ('site', 'Breeding Site'), ('mission', 'Mission'),)
    type = models.CharField(max_length=7, help_text="Type of report: 'adult', 'site', or 'mission'.", )
    mission = models.ForeignKey(Mission, blank=True, null=True)
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


class ReportResponse(models.Model):
    report = models.ForeignKey(Report, related_name='responses', help_text='Report to which this response is ' \
                                                                          'associated.')
    question = models.CharField(max_length=1000, help_text='Question that the user responded to.')
    answer = models.CharField(max_length=1000, help_text='Answer that user selected.')

    def __unicode__(self):
        return str(self.id)


def make_image_uuid(path):
    def wrapper(instance, filename):
        extension = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), extension)
        return os.path.join(path, filename)
    return wrapper


class Photo(models.Model):
    """
    Photo uploaded by user.
    """
    photo = models.ImageField(upload_to=make_image_uuid('tigapics'))
    report = models.ForeignKey(Report)

    def __unicode__(self):
        return self.photo.name


class Fix(models.Model):
    """
    Location fix uploaded by user.
    """
    user = models.ForeignKey(TigaUser)
    fix_time = models.DateTimeField()
    server_upload_time = models.DateTimeField(auto_now_add=True)
    phone_upload_time = models.DateTimeField()
    masked_lon = models.FloatField()
    masked_lat = models.FloatField()
    power = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.user.user_UUID + " " + str(self.fix_time)

    class Meta:
        verbose_name = "fix"
        verbose_name_plural = "fixes"


class Configuration(models.Model):
    """
    anther tes
    p -- jj
    """
    samples_per_day = models.IntegerField(help_text="Number of randomly-timed location samples to take per day.")
    creation_time = models.DateTimeField(help_text='Date and time when this configuration was created by MoveLab. '
                                                   'Automatically generated when record is saved.',
                                         auto_now_add=True)

    def __unicode__(self):
        return str(self.samples_per_day)