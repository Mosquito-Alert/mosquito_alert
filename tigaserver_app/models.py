from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
import json
import firebase_admin.messaging
import firebase_admin._messaging_utils
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Message, Notification as FirebaseNotification, AndroidConfig, AndroidNotification
import logging
from math import floor
from PIL import Image
import pydenticon
import os
from slugify import slugify
from typing import Optional
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance as DistanceMeasure
from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string, TemplateDoesNotExist
from django.urls import reverse
from django.utils import translation
from django.utils.deconstruct import deconstructible
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _

from common.translation import get_translation_in, get_locale_for_native
from tigacrafting.models import MoveLabAnnotation, ExpertReportAnnotation, Categories, STATUS_CATEGORIES
import tigacrafting.html_utils as html_utils
import tigaserver_project.settings as conf

from .managers import ReportManager
from .mixins import TimeZoneModelMixin

logger_report_geolocation = logging.getLogger('mosquitoalert.location.report_location')
logger_notification = logging.getLogger('mosquitoalert.notification')


ACHIEVEMENT_10_REPORTS = 'achievement_10_reports'
ACHIEVEMENT_20_REPORTS = 'achievement_20_reports'
ACHIEVEMENT_50_REPORTS = 'achievement_50_reports'
DAILY_PARTICIPATION = 'daily_participation'
START_OF_SEASON = 'start_of_season'
FIDELITY_DAY_2 = 'fidelity_day_2'
FIDELITY_DAY_3 = 'fidelity_day_3'
ACHIEVEMENT_10_REPORTS_XP = 10
ACHIEVEMENT_20_REPORTS_XP = 20
ACHIEVEMENT_50_REPORTS_XP = 50


def grant_10_reports_achievement( report, granter ):
    grant_special_award(None, report.creation_time, report.user, granter, ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP )


def grant_20_reports_achievement( report, granter ):
    grant_special_award(None, report.creation_time, report.user, granter, ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)


def grant_50_reports_achievement( report, granter ):
    grant_special_award(None, report.creation_time, report.user, granter, ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP)


def grant_first_of_season( report, granter ):
    c = AwardCategory.objects.get(category_label=START_OF_SEASON)
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_first_of_day( report, granter ):
    c = AwardCategory.objects.get(category_label=DAILY_PARTICIPATION)
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_two_consecutive_days_sending( report, granter ):
    c = AwardCategory.objects.get(category_label=FIDELITY_DAY_2)
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_three_consecutive_days_sending(report, granter):
        c = AwardCategory.objects.get(category_label=FIDELITY_DAY_3)
        grant_award(report, report.creation_time, report.user, granter, c)

def get_xp_value_of_category(category_label):
    c = AwardCategory.objects.get(category_label=category_label)
    return c.xp_points

def grant_special_award(for_report, awarded_on_date, awarded_to_tigauser, awarded_by_expert, special_award_label, special_award_xp):
    '''
    :param for_report: Optional
    :param awarded_on_date: Mandatory
    :param awarded_to_tigauser: Mandatory
    :param awarded_by_expert: Mandatory
    :param special_award_label: Mandatory
    :param special_award_xp: Mandatory
    :return:
    '''
    a = Award()
    a.report = for_report
    a.date_given = awarded_on_date
    a.given_to = awarded_to_tigauser
    if awarded_by_expert is not None:
        a.expert = awarded_by_expert
    a.special_award_text = special_award_label
    a.special_award_xp = special_award_xp
    a.save()

def grant_award(for_report, awarded_on_date, awarded_to_tigauser, awarded_by_expert, award_category):
    '''

    :param for_report: Report for which the award is given
    :param awarded_on_date: Date on which the award was granted (usually same as report_creation)
    :param awarded_to_tigauser: User to which it was awarded (usually report owner)
    :param awarded_by_expert: Expert which awarded the report
    :param award_category: Category of the award
    :return:
    '''
    a = Award()
    a.report = for_report
    a.date_given = awarded_on_date
    a.given_to = awarded_to_tigauser
    if awarded_by_expert is not None:
        a.expert = awarded_by_expert
    if award_category is not None:
        a.category = award_category
    a.save()

def get_icon_for_blood_genre(blood_genre) -> str:
    blood_genre_table = {
        BLOOD_GENRE[0][0]: '<label title="Male"><i class="fa fa-mars fa-lg" aria-hidden="true"></i> Male</label>',
        BLOOD_GENRE[1][0]: '<label title="Female"><i class="fa fa-venus fa-lg" aria-hidden="true"></i> Female</label>',
        BLOOD_GENRE[2][0]: '<label title="Female blood"><i class="fa fa-tint fa-lg" aria-hidden="true"></i> Bloodfed</label>',
        BLOOD_GENRE[3][0]: '<label title="Female gravid"><i class="moon" aria-hidden="true"></i> Gravid</label>',
        BLOOD_GENRE[4][0]: '<label title="Female gravid + blood"><i class="moon" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i> Bloodfed and gravid</label>',
        BLOOD_GENRE[5][0]: '<label title="Dont know"><i class="fa fa-question fa-lg" aria-hidden="true"></i> Dont know</label>'
    }
    if blood_genre is None:
        return ''
    else:
        try:
            return str(blood_genre_table[blood_genre])
        except KeyError:
            #return blood_genre_table['dk']
            return ''

def get_translated_species_name(locale,untranslated_species) -> str:
    current_locale = 'en'
    for l in settings.LANGUAGES:
        if locale==l[0]:
            current_locale = locale
    translation.activate(current_locale)
    translations_table_species_name = {
        "Unclassified": _("species_unclassified"),
        "Other species": _("species_other"),
        "Aedes albopictus": _("species_albopictus"),
        "Aedes aegypti": _("species_aegypti"),
        "Aedes japonicus": _("species_japonicus"),
        "Aedes koreicus": _("species_koreicus"),
        "Complex": _("species_complex"),
        "Not sure": _("species_notsure"),
        "Culex sp.": _("species_culex")
    }
    retval = translations_table_species_name.get(untranslated_species, "Unknown")
    translation.deactivate()
    return str(retval)

def get_translated_value_name(locale, untranslated_value) -> str:
    current_locale = 'en'
    for l in settings.LANGUAGES:
        if locale == l[0]:
            current_locale = locale
    translation.activate(current_locale)
    translations_table_value_name = {
        1: _("species_value_possible"),
        2: _("species_value_confirmed")
    }
    retval = translations_table_value_name.get(untranslated_value, "Unknown")
    translation.deactivate()
    return str(retval)

class TigaProfile(models.Model):
    firebase_token = models.TextField('Firebase token associated with the profile', null=True, blank=True,help_text='Firebase token supplied by firebase, suuplied by an registration service (Google, Facebook,etc)', unique=True)
    score = models.IntegerField(help_text='Score associated with profile. This is the score associated with the account', default=0)


class RankingData(models.Model):
    user_uuid = models.CharField(max_length=36, primary_key=True, help_text='User identifier uuid')
    class_value = models.CharField(max_length=60)
    rank = models.IntegerField()
    score_v2 = models.IntegerField()
    last_update = models.DateTimeField(help_text="Last time ranking data was updated", null=True, blank=True)


class TigaUser(models.Model):
    user_UUID = models.CharField(max_length=36, primary_key=True, help_text='UUID randomly generated on '
                                                                            'phone to identify each unique user. Must be exactly 36 '
                                                                            'characters (32 hex digits plus 4 hyphens).')
    registration_time = models.DateTimeField(auto_now_add=True, help_text='The date and time when user '
                                                                      'registered and consented to sharing '
                                                                 'data. Automatically set by '
                                                                 'server when user uploads registration.')
    device_token = models.TextField(help_text='Device token, used in messaging. Must be supplied by the client', null=True, blank=True)

    score = models.IntegerField(help_text='Score associated with user. This field is used only if the user does not have a profile', default=0)

    score_v2 = models.IntegerField(help_text='Global XP Score. This field is updated whenever the user asks for the score, and is only stored here. The content must equal score_v2_adult + score_v2_bite + score_v2_site', default=0)

    score_v2_adult = models.IntegerField(help_text='Adult reports XP Score.', default=0)

    score_v2_bite = models.IntegerField(help_text='Bite reports XP Score.', default=0)

    score_v2_site = models.IntegerField(help_text='Site reports XP Score.',default=0)

    profile = models.ForeignKey(TigaProfile, related_name='profile_devices', null=True, blank=True, on_delete=models.SET_NULL, )

    score_v2_struct = models.TextField(help_text="Full cached score data", null=True, blank=True)

    last_score_update = models.DateTimeField(help_text="Last time score was updated", null=True, blank=True)

    language_iso2 = models.CharField(
        max_length=2,
        default='en',
        help_text="Language setting of app. 2-digit ISO-639-1 language code.",
    )

    def __unicode__(self):
        return self.user_UUID

    def number_of_reports_uploaded(self):
        return Report.objects.filter(user=self).count()

    def is_ios(self):
        return self.user_UUID.isupper()

    def get_identicon(self):
        file_path = settings.MEDIA_ROOT + "/identicons/" + self.user_UUID + ".png"
        if not os.path.exists(file_path):
            generator = pydenticon.Generator(5, 5, foreground=settings.IDENTICON_FOREGROUNDS)
            identicon_png = generator.generate(self.user_UUID, 200, 200, output_format="png")
            f = open(file_path, "wb")
            f.write(identicon_png)
            f.close()
        return settings.MEDIA_URL + "identicons/" + self.user_UUID + ".png"

    n_reports = property(number_of_reports_uploaded)
    ios_user = property(is_ios)

    def save(self, *args, **kwargs):
        if self.device_token:
            # Make sure user is subscribed to global topic
            try:
                global_topic = NotificationTopic.objects.get(topic_code='global')
            except NotificationTopic.DoesNotExist:
                pass
            else:
                UserSubscription.objects.get_or_create(
                    user=self,
                    topic=global_topic
                )

            # Subscribe user to the language selected.
            try:
                language_topic = NotificationTopic.objects.get(topic_code=self.language_iso2)
            except NotificationTopic.DoesNotExist:
                pass
            else:
                UserSubscription.objects.get_or_create(
                    user=self,
                    topic=language_topic
                )
        else:
            if hasattr(self, 'user_subscriptions'):
                for subscription in self.user_subscriptions.all():
                    subscription.delete()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class Mission(models.Model):
    id = models.AutoField(primary_key=True, help_text='Unique identifier of the mission. Automatically generated by ' \
                                                  'server when mission created.')
    title_catalan = models.CharField(max_length=200, help_text='Title of mission in Catalan')
    title_spanish = models.CharField(max_length=200, help_text='Title of mission in Spanish')
    title_english = models.CharField(max_length=200, help_text='Title of mission in English')
    short_description_catalan = models.CharField(max_length=200, help_text='Catalan text to be displayed '
                                                                                       'in mission '
                                                                           'list.')
    short_description_spanish = models.CharField(max_length=200, help_text='Spanish text to be displayed '
                                                                                      'in mission '
                                                                           'list.')
    short_description_english = models.CharField(max_length=200, help_text='English text to be displayed '
                                                                                      'in mission '
                                                                           'list.')
    long_description_catalan = models.CharField(max_length=1000, blank=True, help_text='Catalan text that fully ' \
                                                                                     'explains '
                                                                             'mission '
                                                                           'to '
                                                                           'user')
    long_description_spanish = models.CharField(max_length=1000, blank=True, help_text='Spanish text that fully ' \
                                                                                     'explains mission '
                                                                           'to user')
    long_description_english = models.CharField(max_length=1000, blank=True, help_text='English text that fully ' \
                                                                                     'explains mission '
                                                                           'to user')
    help_text_catalan = models.TextField(blank=True, help_text='Catalan text to be displayed when user taps mission '
                                                               'help '
                                                               'button.')
    help_text_spanish = models.TextField(blank=True, help_text='Spanish text to be displayed when user taps mission '
                                                               'help '
                                                               'button.')
    help_text_english = models.TextField(blank=True, help_text='English text to be displayed when user taps mission '
                                                               'help '
                                                               'button.')
    PLATFORM_CHOICES = (('none', 'No platforms (for drafts)'), ('and', 'Android'), ('ios', 'iOS'), ('html', 'HTML5'), ('beta', 'beta versions only'), ('all',
                                                                                               'All platforms'),)
    platform = models.CharField(max_length=4, choices=PLATFORM_CHOICES, help_text='What type of device is this '
                                                                                   'mission is intended for? It will '
                                                                                   'be sent only to these devices')
    creation_time = models.DateTimeField(auto_now=True, help_text='Date and time mission was created by MoveLab. '
                                                                  'Automatically generated when mission saved.')
    expiration_time = models.DateTimeField(blank=True, null=True, help_text='Optional date and time when mission '
                                                                            'should expire (if ever). Mission will no longer be displayed to users after this date-time.')

    photo_mission = models.BooleanField(help_text='Should this mission allow users to attach photos to their '
                                                  'responses? (True/False).')
    url = models.URLField(blank=True, help_text='Optional URL that wll be displayed to user for this mission. (The '
                                                'entire mission can consist of user going to that URL and performing '
                                                'some action there. For security reasons, this URL must be within a '
                                                'MoveLab domain.')
    mission_version = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.title_catalan

    def active_missions(self):
        return self.expiration_time >= datetime.utcnow().replace(tzinfo=utc)


class MissionTrigger(models.Model):
    mission = models.ForeignKey(Mission, related_name='triggers', on_delete=models.CASCADE, )
    lat_lower_bound = models.FloatField(blank=True, null=True, help_text='Optional lower-bound latitude for '
                                                                         'triggering mission to appear to user. Given in decimal degrees.')
    lat_upper_bound = models.FloatField(blank=True, null=True, help_text='Optional upper-bound latitude for '
                                                                         'triggering mission to appear to user. Given in decimal degrees.')
    lon_lower_bound = models.FloatField(blank=True, null=True, help_text='Optional lower-bound longitude for '
                                                                         'triggering mission to appear to user. Given in decimal degrees.')
    lon_upper_bound = models.FloatField(blank=True, null=True, help_text='Optional upper-bound longitude for '
                                                                         'triggering mission to appear to user. Given in decimal degrees.')
    time_lowerbound = models.TimeField(blank=True, null=True, help_text='Lower bound of optional time-of-day window '
                                                                        'for triggering mission. If '
                                                                        'location trigger also is specified, mission will '
                                                                        'be triggered only '
                                                                        'if user is found in that location within the window; if '
                                                                        'location is not specified, the mission will '
                                                                        'be triggered for all users who have their phones on during the '
                                                                        'time window. Given as time without date, '
                                                                        'formatted as ISO 8601 time string (e.g. '
                                                                        '"12:34:00") with no time zone specified (trigger '
                                                                        'is always based on local time zone of user.)')
    time_upperbound = models.TimeField(blank=True, null=True, help_text='Lower bound of optional time-of-day window '
                                                                        'for triggering mission. If '
                                                                        'location trigger also is specified, mission will '
                                                                        'be triggered only if user is found in that location within the window; if '
                                                                        'location is not specified, the mission will be '
                                                                        'triggered for all users who have their phones on during the '
                                                                        'time window. Given as time without date, '
                                                                        'formatted as ISO 8601 time string (e.g. '
                                                                        '"12:34:00") with no time zone specified (trigger '
                                                                        'is always based on local time zone of user.)')


class MissionItem(models.Model):
    mission = models.ForeignKey(Mission, related_name='items', help_text='Mission to which this item is associated.', on_delete=models.CASCADE, )
    question_catalan = models.CharField(max_length=1000, help_text='Question displayed to user in Catalan.')
    question_spanish = models.CharField(max_length=1000, help_text='Question displayed to user in Spanish.')
    question_english = models.CharField(max_length=1000, help_text='Question displayed to user in English.')
    answer_choices_catalan = models.CharField(max_length=1000, help_text='Response choices in Catalan, wrapped in quotes, comma separated and in square brackets (e.g., ["yes", "no"]).')
    answer_choices_spanish = models.CharField(max_length=1000, help_text='Response choices in Catalan, wrapped in quotes, comma separated and in square brackets (e.g., ["yes", "no"]).')
    answer_choices_english = models.CharField(max_length=1000, help_text='Response choices in Catalan, wrapped in quotes, comma separated and in square brackets (e.g., ["yes", "no"]).')
    help_text_catalan = models.TextField(blank=True, help_text='Catalan help text displayed to user for this item.')
    help_text_spanish = models.TextField(blank=True, help_text='Spanish help text displayed to user for this item.')
    help_text_english = models.TextField(blank=True, help_text='English help text displayed to user for this item.')
    prepositioned_image_reference = models.IntegerField(blank=True, null=True, help_text='Optional image '
                                                                                         'displayed to user '
                                                                                         'within the help '
                                                                                         'message. Integer '
                                                                                         'reference to image '
                                                                                         'prepositioned on device.')
    attached_image = models.ImageField(upload_to='tigaserver_mission_images', blank=True, null=True,
                                       help_text='Optional Image displayed to user within the help message. File.')


class EuropeCountry(models.Model):
    gid = models.IntegerField(primary_key=True)
    cntr_id = models.CharField(max_length=2, blank=True)
    name_engl = models.CharField(max_length=44, blank=True)
    iso3_code = models.CharField(max_length=3, blank=True)
    fid = models.CharField(max_length=2, blank=True)
    geom = models.MultiPolygonField(blank=True, null=True)
    x_min = models.FloatField(blank=True, null=True)
    x_max = models.FloatField(blank=True, null=True)
    y_min = models.FloatField(blank=True, null=True)
    y_max = models.FloatField(blank=True, null=True)
    is_bounding_box = models.BooleanField(default=False, help_text='If true, this geometry acts as a bounding box. The bounding boxes act as little separate entolabs, in the sense that no reports located inside a bounding box should reach an expert outside this bounding box')
    national_supervisor_report_expires_in = models.IntegerField(default=14, help_text='Number of days that a report in the queue is exclusively available to the nagional supervisor. For example, if the field value is 6, after report_creation_time + 6 days a report will be available to all users')

    pending_crisis_reports = models.IntegerField(blank=True, null=True, help_text='Number of reports in country assignable to non-supervisors')
    last_crisis_report_n_update = models.DateTimeField(help_text="Last time count was updated", null=True, blank=True)

    class Meta:
        managed = True
        ordering = ['name_engl']
        db_table = 'europe_countries'

    def __unicode__(self):
        return self.name_engl

    def __str__(self):
        return '{} - {}'.format(self.gid, self.name_engl)

class NutsEurope(models.Model):
    gid = models.AutoField(primary_key=True)
    nuts_id = models.CharField(max_length=5, blank=True, null=True)
    levl_code = models.SmallIntegerField(blank=True, null=True)
    cntr_code = models.CharField(max_length=2, blank=True, null=True)
    name_latn = models.CharField(max_length=70, blank=True, null=True)
    nuts_name = models.CharField(max_length=106, blank=True, null=True)
    mount_type = models.SmallIntegerField(blank=True, null=True)
    urbn_type = models.SmallIntegerField(blank=True, null=True)
    coast_type = models.SmallIntegerField(blank=True, null=True)
    fid = models.CharField(max_length=5, blank=True, null=True)
    geom = models.MultiPolygonField(blank=True, null=True)
    europecountry = models.ForeignKey(EuropeCountry, blank=True, null=True, related_name="nuts", on_delete=models.CASCADE)

    def __str__(self):
        return "{0} ({1})".format(self.name_latn, self.europecountry.name_engl)

    class Meta:
        managed = True
        db_table = 'nuts_europe'


class Session(models.Model):
    id = models.AutoField(primary_key=True, help_text='Unique identifier of the session. Automatically generated by server when session created.')
    session_ID = models.IntegerField(db_index=True, help_text='The session ID number. Should be an integer that increments by 1 for each session from a given user.')
    user = models.ForeignKey(TigaUser, help_text='user_UUID for the user sending this report. Must be exactly 36 characters (32 hex digits plus 4 hyphens) and user must have already registered this ID.', related_name="user_sessions", on_delete=models.CASCADE)
    session_start_time = models.DateTimeField(help_text='Date and time on phone when the session was started. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".')
    session_end_time = models.DateTimeField(null=True, blank=True, help_text='Date and time on phone when the session was ended. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".')

    class Meta:
        unique_together = ('session_ID', 'user',)


class Report(TimeZoneModelMixin, models.Model):
    TYPE_BITE = "bite"
    TYPE_ADULT = "adult"
    TYPE_SITE = "site"
    TYPE_MISSION = "mission"

    TYPE_CHOICES = (
        (TYPE_BITE, _("Bite")),
        (TYPE_ADULT, _("Adult")),
        (TYPE_SITE, _("Breeding Site")),
        (TYPE_MISSION, _("Mission")),
    )

    LOCATION_CURRENT = "current"
    LOCATION_SELECTED = "selected"
    LOCATION_MISSING = "missing"
    LOCATION_CHOICE_CHOICES = (
        (LOCATION_CURRENT, _("Current location detected by user's device")),
        (LOCATION_SELECTED, _("Location selected by user from map")),
        (
            LOCATION_MISSING,
            _("No location choice submitted - should be used only for missions"),
        ),
    )

    # Relations
    user = models.ForeignKey(
        TigaUser,
        on_delete=models.PROTECT,
        related_name="user_reports",
        help_text="user_UUID for the user sending this report. Must be exactly 36 characters (32 hex digits plus 4 hyphens) and user must have already registered this ID.",
    )
    mission = models.ForeignKey(
        Mission,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="If this report was a response to a mission, the unique id field of that mission.",
    )
    country = models.ForeignKey(
        EuropeCountry, on_delete=models.PROTECT, blank=True, null=True
    )
    session = models.ForeignKey(
        Session,
        related_name="session_reports",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Session ID for session in which this report was created",
    )

    # Attributes - Mandatory
    version_UUID = models.CharField(
        primary_key=True,
        max_length=36,
        help_text="UUID randomly generated on phone to identify each unique report version. Must be exactly 36 characters (32 hex digits plus 4 hyphens).",
    )
    version_number = models.IntegerField(
        db_index=True,
        help_text="The report version number. Should be an integer that increments by 1 for each repor version. Note that the user keeps only the most recent version on the device, but all versions are stored on the server.",
    )
    report_id = models.CharField(
        max_length=4,
        db_index=True,
        help_text="4-digit alpha-numeric code generated on user phone to identify each unique report from that user. Digits should lbe randomly drawn from the set of all lowercase and uppercase alphabetic characters and 0-9, but excluding 0, o, and O to avoid confusion if we ever need user to be able to refer to a report ID in correspondence with MoveLab (as was previously the case when we had them sending samples).",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        editable=False,
        help_text="Date and time when the report was last modified",
    )
    server_upload_time = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        editable=False,
        help_text="Date and time on server when report uploaded. (Automatically generated by server.)",
    )
    phone_upload_time = models.DateTimeField(
        help_text="Date and time on phone when it uploaded fix. Format as ECMA 262 date time string (e.g. '2014-05-17T12:34:56.123+01:00'."
    )
    creation_time = models.DateTimeField(
        help_text="Date and time on phone when first version of report was created. Format as ECMA 262 date time string (e.g. '2014-05-17T12:34:56.123+01:00'."
    )
    version_time = models.DateTimeField(
        help_text="Date and time on phone when this version of report was created. Format as ECMA 262 date time string (e.g. '2014-05-17T12:34:56.123+01:00'."
    )
    datetime_fix_offset = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        editable=False,
        help_text="An integer representing the offset (in seconds) applied to the original datetime values for fixing. "
            "If None, it indicates that no information about the original time zone could be inferred or the timezone "
            "was already provided when posting the report. To retrieve the original values, "
            "use: original_value = current_value - datetime_fix_offset."
            "Fields to apply (if necessary) are: 'phone_upload_time', 'creation_time' and 'version_time'."
    )

    type = models.CharField(
        max_length=7,
        choices=TYPE_CHOICES,
        help_text="Type of report: 'adult', 'site', or 'mission'.",
    )

    hide = models.BooleanField(
        default=False, help_text="Hide this report from public views?"
    )

    location_choice = models.CharField(
        max_length=8,
        choices=LOCATION_CHOICE_CHOICES,
        help_text="Did user indicate that report relates to current location of phone ('current') or to a location selected manually on the map ('selected')? Or is the choice missing ('missing')",
    )

    # Attributes - Optional
    current_location_lon = models.FloatField(
        null=True,
        blank=True,
        help_text="Longitude of user's current location. In decimal degrees.",
    )
    current_location_lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Latitude of user's current location. In decimal degrees.",
    )
    selected_location_lon = models.FloatField(
        null=True,
        blank=True,
        help_text="Latitude of location selected by user on map. In decimal degrees.",
    )
    selected_location_lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Longitude of location selected by user on map. In decimal degrees.",
    )
    point = models.PointField(null=True, blank=True, srid=4326)

    note = models.TextField(
        null=True, blank=True, help_text="Note user attached to report."
    )

    nuts_2 = models.CharField(max_length=4, null=True, blank=True)
    nuts_3 = models.CharField(max_length=5, null=True, blank=True)

    ia_filter_1 = models.FloatField(
        null=True,
        blank=True,
        help_text="Value ranging from -1.0 to 1.0 positive values indicate possible insect, negative values indicate spam(non-insect)",
    )
    ia_filter_2 = models.FloatField(
        null=True,
        blank=True,
        help_text="Score for best classified image. 0 indicates not classified, 1.xx indicates classified with score xx, 2.xx classified with alert with score xx.",
    )

    cached_visible = models.IntegerField(
        null=True, blank=True, help_text="Precalculated value of show_on_map_function"
    )

    package_name = models.CharField(
        max_length=400,
        null=True,
        blank=True,
        db_index=True,
        help_text="Name of tigatrapp package from which this report was submitted.",
    )
    package_version = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Version number of tigatrapp package from which this report was submitted.",
    )

    device_manufacturer = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Manufacturer of device from which this report was submitted.",
    )
    device_model = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Model of device from which this report was submitted.",
    )
    os = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Operating system of device from which this report was submitted.",
    )
    os_version = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Operating system version of device from which this report was submitted.",
    )
    os_language = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Language setting of operating system on device from which this report was submitted. 2-digit ISO-639-1 language code.",
    )
    app_language = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Language setting, within tigatrapp, of device from which this report was submitted. 2-digit ISO-639-1 language code.",
    )

    # Object Manager
    objects = ReportManager()

    # Custom Properties
    @property
    def country_label(self) -> str:
        if self.is_spain:
            return "Spain/Other"
        elif self.country:
            return "Europe/" + self.country.name_engl
        else:
            return "Unassigned"

    @property
    def formatted_date(self) -> str:
        return self.version_time.strftime("%d-%m-%Y %H:%M")

    @property
    def deleted(self) -> bool:
        return self.version_number == -1 or self.other_versions.filter(version_number=-1).exists()

    @property
    def latest_version(self) -> bool:
        last_version = Report.objects.filter(
            report_id=self.report_id,
            type=self.type,
            user=self.user
        ).latest("version_number")

        return self.pk == last_version.pk

    @property
    def is_spain(self) -> bool:
        return self.country is None or self.country.gid == 17

    @property
    def language(self) -> str:
        if self.language_code:
            return translation.get_language_info(self.language_code)["name"]
        else:
            return "English"

    @property
    def language_code(self) -> str:
        app_language = self.app_language
        if app_language is not None and app_language != "":
            return app_language
        return "en"

    @property
    def located(self) -> bool:
        return self.lat is not None and self.lon is not None

    @property
    def lat(self) -> Optional[float]:
        if (
            self.location_choice == self.LOCATION_SELECTED
            and self.selected_location_lat is not None
        ):
            return self.selected_location_lat
        else:
            return self.current_location_lat

    @property
    def masked_lat(self) -> Optional[float]:
        if self.lat is not None:
            return round(floor(self.lat / 0.05) * 0.05, 2)
        else:
            return None

    @property
    def lon(self) -> Optional[float]:
        if (
            self.location_choice == self.LOCATION_SELECTED
            and self.selected_location_lon is not None
        ):
            return self.selected_location_lon
        else:
            return self.current_location_lon

    @property
    def masked_lon(self) -> Optional[float]:
        if self.lon is not None:
            return round(floor(self.lon / 0.05) * 0.05, 2)
        else:
            return None

    @property
    def other_versions(self):
        return Report.objects.filter(
            report_id=self.report_id,
            user=self.user,
            type=self.type
        ).exclude(pk=self.pk)

    @property
    def response_html(self) -> str:
        these_responses = self.responses.all().order_by("question")
        result = ""
        for this_response in these_responses:
            result = (
                result
                + "<br/>"
                + this_response.question
                + "&nbsp;"
                + this_response.answer
            )
        return result

    @property
    def response_string(self) -> str:
        these_responses = self.responses.all().order_by("question")
        result = ""
        for this_response in these_responses:
            result = (
                result + "{" + this_response.question + " " + this_response.answer + "}"
            )
        return result

    @property
    def tigaprob(self) -> float:
        response_score = 0
        total = 0
        for response in self.responses.all():
            total += 1
            if "Y" in response.answer or "S" in response.answer:
                response_score += 1
            elif "No" in response.answer:
                response_score -= 1
        if total == 0:
            total = 1
        return float(response_score) / total

    @property
    def tigaprob_cat(self) -> int:
        return int(round(2.499999 * self.tigaprob, 0))

    @property
    def tigaprob_text(self) -> str:
        if self.tigaprob == 1.0:
            return _("High")
        elif 0.0 < self.tigaprob < 1.0:
            return _("Medium")
        else:
            return _("Low")

    @property
    def visible(self) -> bool:
        return self.show_on_map()

    @property
    def visible_photos(self):
        return self.photos.all().exclude(hide=True)

    @property
    def n_visible_photos(self) -> int:
        return self.visible_photos.count()

    @property
    def n_photos(self) -> int:
        return self.photos.all().count()

    @property
    def photo_html(self) -> str:
        result = ""
        for photo in self.visible_photos:
            result = result + photo.small_image_() + "&nbsp;"
        return result

    # Custom properties related to annotations
    @property
    def movelab_annotation_euro(self) -> Optional[dict]:
        expert_validated = ExpertReportAnnotation.objects.filter(
            report=self, user__groups__name="expert", validation_complete=True
        ).count() >= 3 or ExpertReportAnnotation.objects.filter(
            report=self,
            user__groups__name="superexpert",
            validation_complete=True,
            revise=True,
        )
        if self.creation_time.year == 2014 and not expert_validated:
            if self.type == self.TYPE_ADULT:
                max_movelab_annotation = (
                    MoveLabAnnotation.objects.filter(task__photo__report=self)
                    .exclude(hide=True)
                    .order_by("tiger_certainty_category")
                    .last()
                )
                if max_movelab_annotation is not None:
                    return {
                        "tiger_certainty_category": max_movelab_annotation.tiger_certainty_category,
                        "crowdcrafting_score_cat": max_movelab_annotation.task.tiger_validation_score_cat,
                        "crowdcrafting_n_response": max_movelab_annotation.task.crowdcrafting_n_responses,
                        "edited_user_notes": max_movelab_annotation.edited_user_notes,
                        "photo_html": max_movelab_annotation.task.photo.popup_image(),
                    }
        else:
            if expert_validated:
                result = {"edited_user_notes": self.get_final_public_note()}
                if self.get_final_photo_html():
                    result["photo_html"] = self.get_final_photo_html().popup_image()
                if self.type == self.TYPE_ADULT:
                    classification = (
                        self.get_final_combined_expert_category_euro_struct()
                    )
                    if classification["conflict"] is True:
                        result["class_name"] = "Conflict"
                        result["class_label"] = "conflict"
                    else:
                        if classification["category"] is not None:
                            if classification["complex"] is not None:
                                result["class_name"] = classification[
                                    "complex"
                                ].description
                                result["class_label"] = slugify(
                                    classification["category"].name
                                )
                                result["class_id"] = classification["category"].id
                                result["class_value"] = classification["complex"].id
                                # result['class_value'] = classification['value']
                            else:
                                result["class_name"] = classification["category"].name
                                result["class_label"] = slugify(
                                    classification["category"].name
                                )
                                result["class_id"] = classification["category"].id
                                result["class_value"] = classification["value"]
                elif self.type == self.TYPE_SITE:
                    result["class_name"] = "site"
                    result["class_label"] = "site"
                    result["site_certainty_category"] = self.get_final_expert_score()
                return result
        return None

    @property
    def movelab_annotation(self) -> Optional[dict]:
        expert_validated = ExpertReportAnnotation.objects.filter(
            report=self, user__groups__name="expert", validation_complete=True
        ).count() >= 3 or ExpertReportAnnotation.objects.filter(
            report=self,
            user__groups__name="superexpert",
            validation_complete=True,
            revise=True,
        )
        if self.creation_time.year == 2014 and not expert_validated:
            if self.type == self.TYPE_ADULT:
                max_movelab_annotation = (
                    MoveLabAnnotation.objects.filter(task__photo__report=self)
                    .exclude(hide=True)
                    .order_by("tiger_certainty_category")
                    .last()
                )
                if max_movelab_annotation is not None:
                    return {
                        "tiger_certainty_category": max_movelab_annotation.tiger_certainty_category,
                        "crowdcrafting_score_cat": max_movelab_annotation.task.tiger_validation_score_cat,
                        "crowdcrafting_n_response": max_movelab_annotation.task.crowdcrafting_n_responses,
                        "edited_user_notes": max_movelab_annotation.edited_user_notes,
                        "photo_html": max_movelab_annotation.task.photo.popup_image(),
                    }
        else:
            if expert_validated:
                result = {"edited_user_notes": self.get_final_public_note()}
                if self.get_final_photo_html():
                    result["photo_html"] = self.get_final_photo_html().popup_image()
                    if hasattr(self.get_final_photo_html(), "crowdcraftingtask"):
                        result[
                            "crowdcrafting_score_cat"
                        ] = (
                            self.get_final_photo_html().crowdcraftingtask.tiger_validation_score_cat
                        )
                        result[
                            "crowdcrafting_n_response"
                        ] = (
                            self.get_final_photo_html().crowdcraftingtask.crowdcrafting_n_responses
                        )
                if self.type == self.TYPE_ADULT:
                    result["tiger_certainty_category"] = self.get_final_expert_score()
                    result[
                        "aegypti_certainty_category"
                    ] = self.get_final_expert_score_aegypti()
                    classification = self.get_mean_combined_expert_adult_score()
                    result["score"] = int(round(classification["score"]))
                    if result["score"] <= 0:
                        result["classification"] = "none"
                    else:
                        if classification["is_aegypti"] == True:
                            result["classification"] = "aegypti"
                        elif classification["is_albopictus"] == True:
                            result["classification"] = "albopictus"
                        elif classification["is_none"] == True:
                            result["classification"] = "none"
                        else:
                            # This should NEVER happen. however...
                            result["classification"] = "conflict"
                elif self.type == self.TYPE_SITE:
                    result["site_certainty_category"] = self.get_final_expert_score()
                return result
        return None

    @property
    def simplified_annotation(self) -> Optional[dict]:
        if ExpertReportAnnotation.objects.filter(
            report=self, user__groups__name="expert", validation_complete=True
        ).count() >= 3 or ExpertReportAnnotation.objects.filter(
            report=self,
            user__groups__name="superexpert",
            validation_complete=True,
            revise=True,
        ):
            result = {}
            if self.type == self.TYPE_ADULT:
                classification = self.get_mean_combined_expert_adult_score()
                result["score"] = int(round(classification["score"]))
                if classification["is_aegypti"] == True:
                    result["classification"] = "aegypti"
                elif classification["is_albopictus"] == True:
                    result["classification"] = "albopictus"
                elif classification["is_none"] == True:
                    result["classification"] = "none"
                else:
                    # This should NEVER happen. however...
                    result["classification"] = "conflict"
            return result
        return None

    @property
    def movelab_score(self) -> Optional[int]:
        if self.type != self.TYPE_ADULT:
            return None
        max_movelab_annotation = (
            MoveLabAnnotation.objects.filter(task__photo__report=self)
            .exclude(hide=True)
            .order_by("tiger_certainty_category")
            .last()
        )
        if max_movelab_annotation is None:
            return None
        return max_movelab_annotation.tiger_certainty_category

    @property
    def crowd_score(self):
        if self.type != self.TYPE_ADULT:
            return None
        max_movelab_annotation = (
            MoveLabAnnotation.objects.filter(task__photo__report=self)
            .exclude(hide=True)
            .order_by("tiger_certainty_category")
            .last()
        )
        if max_movelab_annotation is None:
            return None
        return max_movelab_annotation.task.tiger_validation_score_cat

    # Custom properties related to breeding sites
    @property
    def basins(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = (
                    this_response.answer.startswith("Basin")
                    or this_response.answer.startswith("Basses")
                    or this_response.answer.startswith("Balsa")
                    or this_response.answer.startswith("Bassa")
                    or this_response.answer.startswith("Small basin")
                    or "balsas" in this_response.answer
                )
        return result

    @property
    def buckets(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = (
                    this_response.answer.startswith("Bucket")
                    or this_response.answer.startswith("Small container")
                    or this_response.answer.startswith("Bidones")
                    or this_response.answer.startswith("Recipiente")
                    or this_response.answer.startswith("Recipient")
                    or this_response.answer.startswith("Bidons")
                )
        return result

    @property
    def embornals(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if this_response.question_id == 12 and this_response.answer_id == 121:
                return True
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
                or this_response.question.startswith("Is this a storm drain")
                or this_response.question.startswith("\xc9s un embornal")
                or this_response.question.startswith("\xbfEs un imbornal")
            ):
                result = (
                    this_response.answer.startswith("Embornal")
                    or this_response.answer.startswith("Sumidero")
                    or this_response.answer.startswith("Storm")
                    or this_response.answer.startswith("Yes")
                    or this_response.answer.startswith("S\xed")
                )
        return result

    @property
    def fonts(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = (
                    this_response.answer.startswith("Font")
                    or this_response.answer.startswith("Fountain")
                    or this_response.answer.startswith("Fuente")
                )
        return result

    @property
    def other(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = (
                    this_response.answer == "Other"
                    or this_response.answer == "Altres"
                    or this_response.answer == "Otros"
                )
        return result

    @property
    def wells(self) -> bool:
        result = False
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = (
                    this_response.answer == "Well"
                    or this_response.answer == "Pozos"
                    or this_response.answer == "Pous"
                )
        return result

    @property
    def site_type(self) -> str:
        result = ""
        for this_response in self.responses.all():
            if (
                this_response.question.startswith("Tipo")
                or this_response.question.startswith("Selecciona")
                or this_response.question.startswith("Type")
            ):
                result = this_response.answer
        return result

    @property
    def site_cat(self) -> int:
        if self.embornals:
            return 0
        elif self.fonts:
            return 1
        elif self.basins:
            return 2
        elif self.buckets:
            return 3
        elif self.wells:
            return 4
        else:
            return 5

    @property
    def site_type_trans(self) -> str:
        if self.embornals:
            return _("storm-drain")
        if self.fonts:
            return _("Fountain")
        if self.basins:
            return _("Basin")
        if self.wells:
            return _("Well")
        if self.other:
            return _("Other")

    # Other properties
    @property
    def tiger_responses_text(self) -> Optional[dict]:
        if self.type != self.TYPE_ADULT:
            return None
        these_responses = self.responses.all()
        result = {}
        for response in these_responses:
            result[response.question] = response.answer
        return result

    @property
    def site_responses_text(self) -> Optional[dict]:
        if self.type != self.TYPE_SITE:
            return None
        these_responses = self.responses.all()
        result = {}
        for response in these_responses:
            result[response.question] = response.answer
        return result

    @property
    def tiger_responses(self) -> Optional[dict]:
        if self.type != self.TYPE_ADULT:
            return None
        these_responses = self.responses.all()
        result = {}
        if (
            these_responses.filter(
                Q(question="Is it small and black with white stripes?")
                | Q(question="\xc9s petit i negre amb ratlles blanques?")
                | Q(question="\xbfEs peque\xf1o y negro con rayas blancas?")
            ).count()
            > 0
        ):
            q1r = these_responses.get(
                Q(question="Is it small and black with white stripes?")
                | Q(question="\xc9s petit i negre amb ratlles blanques?")
                | Q(question="\xbfEs peque\xf1o y negro con rayas blancas?")
            ).answer
            result["q1_response"] = (
                1 if q1r in ["S\xed", "Yes"] else -1 if q1r == "No" else 0
            )
        if (
            these_responses.filter(
                Q(question="Does it have a white stripe on the head and thorax?")
                | Q(question="T\xe9 una ratlla blanca al cap i al t\xf2rax?")
                | Q(question="\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?")
            ).count()
            > 0
        ):
            q2r = these_responses.get(
                Q(question="Does it have a white stripe on the head and thorax?")
                | Q(question="T\xe9 una ratlla blanca al cap i al t\xf2rax?")
                | Q(question="\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?")
            ).answer
            result["q2_response"] = (
                1 if q2r in ["S\xed", "Yes"] else -1 if q2r == "No" else 0
            )
        if (
            these_responses.filter(
                Q(question="Does it have white stripes on the abdomen and legs?")
                | Q(question="T\xe9 ratlles blanques a l'abdomen i a les potes?")
                | Q(question="\xbfTiene rayas blancas en el abdomen y en las patas?")
            ).count()
            > 0
        ):
            q3r = these_responses.get(
                Q(question="Does it have white stripes on the abdomen and legs?")
                | Q(question="T\xe9 ratlles blanques a l'abdomen i a les potes?")
                | Q(question="\xbfTiene rayas blancas en el abdomen y en las patas?")
            ).answer
            result["q3_response"] = (
                1 if q3r in ["S\xed", "Yes"] else -1 if q3r == "No" else 0
            )
        return result

    @property
    def site_responses(self) -> Optional[dict]:
        if self.type != self.TYPE_SITE:
            return None
        these_responses = self.responses.all()
        result = {}
        if self.package_name == "ceab.movelab.tigatrapp" and self.package_version >= 10:
            if (
                these_responses.filter(
                    Q(question="Is it in a public area?")
                    | Q(question="\xbfSe encuentra en la v\xeda p\xfablica?")
                    | Q(question="Es troba a la via p\xfablica?")
                ).count()
                > 0
            ):
                q1r = these_responses.get(
                    Q(question="Is it in a public area?")
                    | Q(question="\xbfSe encuentra en la v\xeda p\xfablica?")
                    | Q(question="Es troba a la via p\xfablica?")
                ).answer
                result["q1_response_new"] = 1 if q1r in ["S\xed", "Yes"] else -1

            if (
                these_responses.filter(
                    Q(
                        question="Does it contain stagnant water and/or mosquito larvae or pupae (any mosquito species)?"
                    )
                    | Q(
                        question="Contiene agua estancada y/o larvas o pupas de mosquito (cualquier especie)?"
                    )
                    | Q(
                        question="Cont\xe9 aigua estancada y/o larves o pupes de mosquit (qualsevol esp\xe8cie)?"
                    )
                ).count()
                > 0
            ):
                q2r = these_responses.get(
                    Q(
                        question="Does it contain stagnant water and/or mosquito larvae or pupae (any mosquito species)?"
                    )
                    | Q(
                        question="Contiene agua estancada y/o larvas o pupas de mosquito (cualquier especie)?"
                    )
                    | Q(
                        question="Cont\xe9 aigua estancada y/o larves o pupes de mosquit (qualsevol esp\xe8cie)?"
                    )
                ).answer
                result["q2_response_new"] = (
                    1 if ("S\xed" in q2r or "Yes" in q2r) else -1
                )

            if (
                these_responses.filter(
                    Q(question="Have you seen adult mosquitoes nearby (<10 meters)?")
                    | Q(question="\xbfHas visto mosquitos cerca (a <10 metros)?")
                    | Q(question="Has vist mosquits a prop (a <10metres)?")
                ).count()
                > 0
            ):
                q3r = these_responses.get(
                    Q(question="Have you seen adult mosquitoes nearby (<10 meters)?")
                    | Q(question="\xbfHas visto mosquitos cerca (a <10 metros)?")
                    | Q(question="Has vist mosquits a prop (a <10metres)?")
                ).answer
                result["q3_response_new"] = 1 if q3r in ["S\xed", "Yes"] else -1
            return result
        else:
            if (
                these_responses.filter(
                    Q(question="Does it have stagnant water inside?")
                    | Q(question="\xbfContiene agua estancada?")
                    | Q(question="Cont\xe9 aigua estancada?")
                ).count()
                > 0
            ):
                q1r = these_responses.get(
                    Q(question="Does it have stagnant water inside?")
                    | Q(question="\xbfContiene agua estancada?")
                    | Q(question="Cont\xe9 aigua estancada?")
                ).answer
                result["q1_response"] = (
                    1 if q1r in ["S\xed", "Yes"] else -1 if q1r == "No" else 0
                )
            if (
                these_responses.filter(
                    Q(
                        question="Have you seen mosquito larvae (not necessarily tiger mosquito) inside?"
                    )
                    | Q(
                        question="\xbfContiene larvas o pupas de mosquito (de cualquier especie)?"
                    )
                    | Q(
                        question="Cont\xe9 larves o pupes de mosquit (de qualsevol esp\xe8cie)?"
                    )
                ).count()
                > 0
            ):
                q2r = these_responses.get(
                    Q(
                        question="Have you seen mosquito larvae (not necessarily tiger mosquito) inside?"
                    )
                    | Q(
                        question="\xbfContiene larvas o pupas de mosquito (de cualquier especie)?"
                    )
                    | Q(
                        question="Cont\xe9 larves o pupes de mosquit (de qualsevol esp\xe8cie)?"
                    )
                ).answer
                result["q2_response"] = (
                    1 if q2r in ["S\xed", "Yes"] else -1 if q2r == "No" else 0
                )
            return result

    @property
    def creation_year(self) -> int:
        return self.creation_time.year

    @property
    def creation_month(self) -> int:
        return self.creation_time.month

    @property
    def creation_date(self):
        return self.creation_time.date()

    @property
    def creation_day_since_launch(self) -> int:
        return (self.creation_time - settings.START_TIME).days

    # Methods
    # See TimeZoneModelMixin
    def _get_latitude_for_timezone(self):
        # By default taking the current_location which is the one provided by the phone
        # If it's not available, and user has selected a specific location, will use that.
        # NOTE: we are assuming the risk of user selecting a location with a different
        #       timezone than the one where the mobile is at that moment.
        #       Only valid for datetimes taken from the phone system, not being possible
        #       for the user to edit.
        return (
            self.selected_location_lat
            if not self.current_location_lat and self.location_choice == self.LOCATION_SELECTED
            else self.current_location_lat
        )

    def _get_longitude_for_timezone(self):
        # By default taking the current_location which is the one provided by the phone
        # If it's not available, and user has selected a specific location, will use that.
        # NOTE: we are assuming the risk of user selecting a location with a different
        #       timezone than the one where the mobile is at that moment.
        #       Only valid for datetimes taken from the phone system, not being possible
        #       for the user to edit.
        return (
            self.selected_location_lon
            if not self.current_location_lon and self.location_choice == self.LOCATION_SELECTED
            else self.current_location_lon
        )

    def _get_country_is_in(self) -> Optional[EuropeCountry]:
        logger_report_geolocation.debug(
            "retrieving country for report with id {0}".format(self.pk)
        )

        if not self.point:
            logger_report_geolocation.debug(
                "report with id {0} has no associated geolocation".format(self.pk)
            )
            return None

        max_distance = DistanceMeasure(km=11.1)  # 0.1 degrees
        country = (
            EuropeCountry.objects.annotate(
                distance=DistanceFunction("geom", self.point)
            )
            .filter(distance__lt=max_distance)
            .order_by("distance")
            .first()
        )

        if country:
            if country.distance.m == 0:
                # Case point is contained (distance = 0 meters)
                logger_report_geolocation.debug(
                    "report with id {0} has SINGLE candidate, country {1} with code {2}".format(
                        self.pk, country.name_engl, country.iso3_code
                    )
                )
            else:
                # Case point was not cointained, but near
                logger_report_geolocation.debug(
                    "report with id {0} assigned to NEARBY country {1} with code {2}".format(
                        self.pk, country.name_engl, country.iso3_code
                    )
                )
        else:
            logger_report_geolocation.debug(
                "report with id {0} found no NEARBY countries, setting country as none".format(
                    self.pk
                )
            )

        return country

    def _get_nuts_is_in(self, levl_code) -> Optional[NutsEurope]:
        if not self.country or not self.point:
            return

        max_distance = DistanceMeasure(km=11.1)  # 0.1 degrees
        nuts = (
            NutsEurope.objects.filter(europecountry=self.country, levl_code=levl_code)
            .annotate(distance=DistanceFunction("geom", self.point))
            .filter(distance__lt=max_distance)
            .order_by("distance")
            .first()
        )

        return nuts

    def _get_point(self) -> Optional[GEOSGeometry]:
        if (self.lon == -1 and self.lat == -1) or self.lon is None or self.lat is None:
            return None
        # longitude, latitude
        wkt_point = "POINT( {0} {1} )"
        p = GEOSGeometry(wkt_point.format(self.lon, self.lat), srid=4326)
        return p

    def save(self, *args, **kwargs):
        # Recreate the Point (just in case lat/lon has changed)
        _old_point = self.point
        self.point = self._get_point()

        # Fill the country field
        if not self.country or _old_point != self.point:
            self.country = self._get_country_is_in()
            if not self.country:
                logger_report_geolocation.debug(
                    "report with id {0} assigned to no country".format(self.pk)
                )
            else:
                logger_report_geolocation.debug(
                    "report with id {0} assigned to country {1} with code {2}".format(
                        self.pk, self.country.name_engl, self.country.iso3_code
                    )
                )

        if self.point and self.country:
            nuts3 = self._get_nuts_is_in(levl_code=3)
            if nuts3:
                self.nuts_3 = nuts3.nuts_id

            nuts2 = self._get_nuts_is_in(levl_code=2)
            if nuts2:
                self.nuts_2 = nuts2.nuts_id

        if self.app_language:
            self.user.language_iso2 = self.app_language
            self.user.save(update_fields=['language_iso2'])

        super(Report, self).save(*args, **kwargs)

    # Meta and String
    class Meta:
        pass

    def __unicode__(self):
        return self.pk



    def get_photo_html_for_report_validation_completed(self):
        result = ''
        for photo in self.visible_photos:
            best_photo = ExpertReportAnnotation.objects.filter(best_photo=photo).exists()
            border_style = "3px solid green" if best_photo else "1px solid #333333"
            result += '<div id="' + str(photo.id) + '" style="border: ' + border_style + ';margin:1px;">' + photo.medium_image_for_validation_() + '</div><div>' + get_icon_for_blood_genre(photo.blood_genre) + '</div><br>'
        return result

    def get_which_is_latest(self):
        all_versions = Report.objects.filter(report_id=self.report_id).order_by('version_number')
        return all_versions.reverse()[0].pk

    def get_crowdcrafting_score(self):
        if self.type not in (self.TYPE_SITE, self.TYPE_ADULT):
            return None
        these_photos = self.photos.exclude(hide=True).annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
        if these_photos.count() == 0:
            return None
        if self.type == self.TYPE_SITE:
            scores = map(lambda x: x.crowdcraftingtask.site_validation_score, these_photos.iterator())
        else:
            scores = map(lambda x: x.crowdcraftingtask.tiger_validation_score, these_photos.iterator())
        if scores is None or len(scores) == 0:
            return None
        else:
            return max(scores)

    def get_is_crowd_validated(self):
        if self.get_crowdcrafting_score():
            return self.get_crowdcrafting_score() > settings.CROWD_VALIDATION_CUTOFF
        else:
            return False

    def get_is_crowd_contravalidated(self):
        if self.get_crowdcrafting_score():
            return self.get_crowdcrafting_score() <= settings.CROWD_VALIDATION_CUTOFF
        else:
            return False

    def get_validated_photo_html(self):
        result = ''
        if self.type not in (self.TYPE_SITE, self.TYPE_ADULT):
            return result
        these_photos = self.photos.exclude(hide=True).annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
        for photo in these_photos:
            result += '<br>' + photo.small_image_() + '<br>'
        return result

    def show_on_map(self) -> bool:
        if self.creation_time.year == 2014:
            return True
        else:
            if self.cached_visible is None:
                return (not self.photos.all().exists()) or ((ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists()) and self.get_final_expert_status() == 1)
            else:
                return self.cached_visible == 1

    def get_mean_expert_adult_score_aegypti(self):
        sum_scores = 0
        mean_score = -3
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, aegypti_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, aegypti_certainty_category__isnull=False).count() == 0:
            return -3
        super_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exclude(aegypti_certainty_category__isnull=True).values_list('aegypti_certainty_category', flat=True)
        if super_scores:
            for this_score in super_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores / float(super_scores.count())
            return mean_score
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, aegypti_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, aegypti_certainty_category__isnull=False).count() == 0:
            return -3
        expert_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).exclude(aegypti_certainty_category__isnull=True).values_list('aegypti_certainty_category', flat=True)
        if expert_scores:
            for this_score in expert_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores/float(expert_scores.count())
        return mean_score

    def get_mean_expert_adult_score(self):
        sum_scores = 0
        mean_score = -3
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True,tiger_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True,tiger_certainty_category__isnull=False).count() == 0:
            return -3
        super_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True).exclude(tiger_certainty_category__isnull=True).values_list('tiger_certainty_category', flat=True)
        if super_scores:
            for this_score in super_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores / float(super_scores.count())
            return mean_score
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,tiger_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,tiger_certainty_category__isnull=False).count() == 0:
            return -3
        expert_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).exclude(tiger_certainty_category__isnull=True).values_list('tiger_certainty_category', flat=True)
        if expert_scores:
            for this_score in expert_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores / float(expert_scores.count())
        return mean_score

    def get_mean_expert_adult_classification_data(self):

        status = {}

        status['unclassified_by_superexpert'] = False
        status['unclassified_by_all_experts'] = False

        status['albopictus_classified_by_superexpert'] = False
        status['albopictus_classified_by_expert'] = False
        status['albopictus_superexpert_classification_count'] = -5
        status['albopictus_superexpert_classification_score'] = -5
        status['albopictus_expert_classification_count'] = -5
        status['albopictus_expert_classification_score'] = -5
        status['albopictus_final_score'] = -5

        status['aegypti_classified_by_superexpert'] = False
        status['aegypti_classified_by_expert'] = False
        status['aegypti_superexpert_classification_count'] = -5
        status['aegypti_superexpert_classification_score'] = -5
        status['aegypti_expert_classification_count'] = -5
        status['aegypti_expert_classification_score'] = -5
        status['aegypti_final_score'] = -5

        #Both unclassified - superexpert
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True,tiger_certainty_category__isnull=True).count() > 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True,tiger_certainty_category__isnull=False).count() == 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True,aegypti_certainty_category__isnull=True).count() > 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True,aegypti_certainty_category__isnull=False).count() == 0:
            status['unclassified_by_superexpert'] = True
            status['albopictus_final_score'] = -3
            status['aegypti_final_score'] = -3

        # Both unclassified - expert
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,tiger_certainty_category__isnull=True).count() > 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,tiger_certainty_category__isnull=False).count() == 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,aegypti_certainty_category__isnull=True).count() > 0 and \
                        ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,aegypti_certainty_category__isnull=False).count() == 0:
            status['unclassified_by_all_experts'] = True
            status['albopictus_final_score'] = -3
            status['aegypti_final_score'] = -3

        #Classified Albopictus - superexpert
        super_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True).exclude(tiger_certainty_category__isnull=True).values_list('tiger_certainty_category', flat=True)
        superexpert_score_num = 0
        sum_scores = 0
        mean_score = -3
        if super_scores:
            for this_score in super_scores:
                #if this_score:
                status['albopictus_classified_by_superexpert'] = True
                superexpert_score_num = superexpert_score_num + 1
                sum_scores += this_score
            mean_score = sum_scores / float(super_scores.count())
        status['albopictus_superexpert_classification_count'] = superexpert_score_num
        status['albopictus_superexpert_classification_score'] = mean_score
        status['albopictus_final_score'] = mean_score

        #Classified Aegypti - superexpert
        super_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True).exclude(aegypti_certainty_category__isnull=True).values_list('aegypti_certainty_category', flat=True)
        superexpert_score_num = 0
        sum_scores = 0
        mean_score = -3
        if super_scores:
            for this_score in super_scores:
                #if this_score:
                status['aegypti_classified_by_superexpert'] = True
                superexpert_score_num = superexpert_score_num + 1
                sum_scores += this_score
            mean_score = sum_scores / float(super_scores.count())
        status['aegypti_superexpert_classification_count'] = superexpert_score_num
        status['aegypti_superexpert_classification_score'] = mean_score
        status['aegypti_final_score'] = mean_score

        #Classified Albopictus - expert
        expert_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).exclude(tiger_certainty_category__isnull=True).values_list('tiger_certainty_category', flat=True)
        expert_score_num = 0
        sum_scores = 0
        mean_score = -3
        if expert_scores:
            for this_score in expert_scores:
                #if this_score:
                status['albopictus_classified_by_expert'] = True
                expert_score_num = expert_score_num + 1
                sum_scores += this_score
            mean_score = sum_scores / float(expert_scores.count())
        status['albopictus_expert_classification_count'] = expert_score_num
        status['albopictus_expert_classification_score'] = mean_score
        if status['albopictus_classified_by_superexpert'] == False:
            status['albopictus_final_score'] = mean_score

        #Classified Aegypti - expert
        expert_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).exclude(aegypti_certainty_category__isnull=True).values_list('aegypti_certainty_category', flat=True)
        expert_score_num = 0
        sum_scores = 0
        mean_score = -3
        if expert_scores:
            for this_score in expert_scores:
                #if this_score:
                status['aegypti_classified_by_expert'] = True
                expert_score_num += 1
                sum_scores += this_score
            mean_score = sum_scores / float(expert_scores.count())
        status['aegypti_expert_classification_count'] = expert_score_num
        status['aegypti_expert_classification_score'] = mean_score
        if status['aegypti_classified_by_superexpert'] == False:
            status['aegypti_final_score'] = mean_score

        return status

    def get_final_combined_expert_category_public_map_euro(self, locale):
        classification = self.get_final_combined_expert_category_euro_struct()
        # retval = {
        #     'category': None,
        #     'complex': None,
        #     'value': None,
        #     'conflict': False,
        #     'in_progress': False
        # }
        if classification['category'] is not None:
            c = classification['category']
            untranslated_category = c.name
            if c.id == 8:
                if classification['complex'] is not None:
                    complex = classification['complex']
                    untranslated_complex = complex.description
                    return untranslated_complex
                else:
                    return "N/A"
            else:
                if c.specify_certainty_level == True:
                    untranslated_certainty = classification['value']
                    return get_translated_species_name(locale,untranslated_category) + " - " + get_translated_value_name(locale,untranslated_certainty)
                else:
                    return get_translated_species_name(locale,untranslated_category)

    def get_most_voted_category(self, expert_annotations):
        most_frequent_item, most_frequent_count = None, 0
        n_blanks = 0
        blank_category = None
        score_table = {}
        for anno in expert_annotations:
            item = anno.category if anno.complex is None else anno.complex
            if item.__class__.__name__ == 'Categories' and item.id == 9:
                blank_category = item
                n_blanks += 1
                pass
            else:
                score_table[item] = score_table.get(item,0) + 1
                if score_table[item] >= most_frequent_count:
                    most_frequent_count, most_frequent_item = score_table[item], item
        if n_blanks == len(expert_annotations):
            return blank_category
        else:
            for key in score_table:
                score = score_table[key]
                if key != most_frequent_item and score >= most_frequent_count:
                    return None  # conflict
        return most_frequent_item

    def get_score_for_category_or_complex(self, category):
        superexpert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True, category=category)
        expert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True, category=category)
        mean_score = -1
        if superexpert_annotations.count() > 0:
            cumulative_score = 0
            for ano in superexpert_annotations:
                cumulative_score += ano.validation_value
            mean_score = cumulative_score/float(superexpert_annotations.count())
        else:
            cumulative_score = 0
            for ano in expert_annotations:
                cumulative_score += ano.validation_value
            mean_score = cumulative_score / float(expert_annotations.count())
        if mean_score > 1.5:
            return 2
        else:
            return 1
        #return mean_score

    def get_html_color_for_label(self):
        label = self.get_final_combined_expert_category_euro()
        return html_utils.get_html_color_for_label(label)

    # if superexpert has opinion then
    #   if more than 1 superexpert has opinion then
    #       consensuate superexpert opinion
    #       return consensuate opinion
    #   else just one expert has opinion then
    #       return superexpert opinion
    # else, check if more than 3 experts said something then
    #   if at least 3 experts have opinion then
    #       consensuate expert opinion
    #       return consensuate opinion
    #   else not yet validated
    #       return not yet validated
    # else no one has opinion then
    #   return not yet validated
    def get_final_combined_expert_category_euro(self):
        superexpert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True,revise=True, category__isnull=False)
        expert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, category__isnull=False)
        most_voted = None
        if superexpert_annotations.count() > 1:
            most_voted = self.get_most_voted_category(superexpert_annotations)
        elif superexpert_annotations.count() == 1:
            if superexpert_annotations[0].category.id == 8:
                most_voted = superexpert_annotations[0].complex
            else:
                most_voted = superexpert_annotations[0].category
        elif expert_annotations.count() >= 3:
            most_voted = self.get_most_voted_category(expert_annotations)
        else:
            return "Unclassified"
        if most_voted is None:
            return "Conflict"
        else:
            if most_voted.__class__.__name__ == 'Categories':
                if most_voted.specify_certainty_level == True:
                    score = self.get_score_for_category_or_complex(most_voted)
                    if score == 2:
                        return "Definitely " + most_voted.name
                    else:
                        return "Probably " + most_voted.name
                else:
                    return most_voted.name
            elif most_voted.__class__.__name__ == 'Complex':
                return most_voted.description

    # This is just a formatter of get_final_combined_expert_category_euro_struct. Takes the exact same output and makes it
    # template friendly, also adds explicit ids for category and complex
    def get_final_combined_expert_category_euro_struct_json(self):
        original_struct = self.get_final_combined_expert_category_euro_struct()
        retval = {
            'category' : None,
            'category_id': None,
            'complex': None,
            'complex_id': None,
            'value': None,
            'conflict': False,
            'in_progress': False
        }
        if original_struct.get('category',None) is not None:
            retval['category_id'] = str(original_struct['category'].id)
            retval['category'] = original_struct['category'].name
        if original_struct.get('complex', None) is not None:
            retval['complex_id'] = str(original_struct['complex'].id)
            retval['complex'] = original_struct['complex'].description

        if original_struct['value'] is not None:
            retval['value'] = str(original_struct['value'])
        retval['conflict'] = original_struct['conflict']
        retval['in_progress'] = original_struct['in_progress']

        return json.dumps(retval)

    def get_final_combined_expert_category_euro_struct(self):
        superexpert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True, category__isnull=False)
        expert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, category__isnull=False)
        retval = {
            'category' : None,
            'complex': None,
            'value': None,
            'conflict': False,
            'in_progress': False
        }
        most_voted = None
        if superexpert_annotations.count() > 1:
            most_voted = self.get_most_voted_category(superexpert_annotations)
        elif superexpert_annotations.count() == 1:
            if superexpert_annotations[0].category.id == 8:
                most_voted = superexpert_annotations[0].complex
            else:
                most_voted = superexpert_annotations[0].category
        elif expert_annotations.count() >= 3:
            most_voted = self.get_most_voted_category(expert_annotations)
        else:
            most_voted = Categories.objects.get(name='Unclassified')
            retval['in_progress'] = True

        if most_voted is None:
            retval['conflict'] = True
        else:
            if most_voted.__class__.__name__ == 'Categories':
                retval['category'] = most_voted
                if most_voted.specify_certainty_level == True:
                    score = self.get_score_for_category_or_complex(most_voted)
                    retval['value'] = score
            elif most_voted.__class__.__name__ == 'Complex':
                retval['complex'] = most_voted
                retval['category'] = Categories.objects.get(pk=8)
        return retval

    def get_mean_combined_expert_adult_score(self):
        status = self.get_mean_expert_adult_classification_data()
        albopictus_score = status['albopictus_final_score']
        aegypti_score = status['aegypti_final_score']

        classification = {}

        classification['is_aegypti'] = False
        classification['is_albopictus'] = False
        classification['is_none'] = False
        classification['conflict'] = False
        classification['score'] = -4

        if status['unclassified_by_superexpert'] == True:
            classification['is_none'] = True
            classification['score'] = -3
            #return -3
        else:
            #unclassified by everyone
            if status['unclassified_by_all_experts'] == True and status['unclassified_by_superexpert'] == True:
                classification['is_none'] = True
                classification['score'] = -3
            elif status['unclassified_by_all_experts'] == True and status['unclassified_by_superexpert'] == False:
                if status['albopictus_classified_by_superexpert'] == True:
                    classification['is_albopictus'] = True
                    classification['score'] = status['albopictus_superexpert_classification_score']
                elif status['aegypti_classified_by_superexpert'] == True:
                    classification['is_aegypti'] = True
                    classification['score'] = status['aegypti_superexpert_classification_score']
                else:
                    classification['is_none'] = True
                    classification['score'] = -3
                #return -3
            else: #Not left null by experts or superexperts
                #Classified either way by superexpert
                if status['aegypti_classified_by_superexpert'] == True and status['albopictus_classified_by_superexpert'] == False:
                    classification['is_aegypti'] = True
                    classification['score'] = status['aegypti_superexpert_classification_score']
                    #return status['aegypti_superexpert_classification_score']
                elif status['aegypti_classified_by_superexpert'] == False and status['albopictus_classified_by_superexpert'] == True:
                    classification['is_albopictus'] = True
                    classification['score'] = status['albopictus_superexpert_classification_score']
                    #return status['albopictus_superexpert_classification_score']
                elif status['aegypti_classified_by_superexpert'] == True and status['albopictus_classified_by_superexpert'] == True:
                    if status['aegypti_superexpert_classification_score'] <= 0 and status['albopictus_superexpert_classification_score'] <= 0:
                        classification['is_none'] = True
                        classification['score'] = status['albopictus_superexpert_classification_score']
                    elif status['aegypti_superexpert_classification_score'] > 0 and status['albopictus_superexpert_classification_score'] <= 0:
                        classification['is_aegypti'] = True
                        classification['score'] = status['aegypti_superexpert_classification_score']
                    elif status['aegypti_superexpert_classification_score'] <= 0 and status['albopictus_superexpert_classification_score'] > 0:
                        classification['is_albopictus'] = True
                        classification['score'] = status['albopictus_superexpert_classification_score']
                    else:
                        # Only possible if more than one superexpert and they say opposite things -> BAD
                        classification['conflict'] = True
                        classification['score'] = -4
                else:  # Neither species classified by superexpert
                    if albopictus_score >= 0 and aegypti_score >= 0: #conflict -> experts reasonably sure they are different species - i.e
                        if status['albopictus_expert_classification_count'] > status['aegypti_expert_classification_count']:
                            classification['is_albopictus'] = True
                            classification['score'] = status['albopictus_expert_classification_score']
                            #return status['albopictus_expert_classification_score']
                        elif status['albopictus_expert_classification_count'] < status['aegypti_expert_classification_count']:
                            classification['is_aegypti'] = True
                            classification['score'] = status['aegypti_expert_classification_score']
                            #return status['aegypti_expert_classification_score']
                        elif status['albopictus_expert_classification_count'] == status['aegypti_expert_classification_count'] and albopictus_score == aegypti_score:
                            if albopictus_score > 0:
                                classification['conflict'] = True
                                classification['score'] = -4
                            else:
                                classification['is_none'] = True
                                classification['score'] = albopictus_score
                        else:#conflict
                            classification['conflict'] = True
                            classification['score'] = -4
                            #return -4
                    elif albopictus_score > 0 and aegypti_score <= 0:
                        if aegypti_score == -3:
                            classification['is_albopictus'] = True
                            classification['score'] = status['albopictus_expert_classification_score']
                            #return status['albopictus_expert_classification_score']
                        else:
                            if status['albopictus_expert_classification_count'] > status['aegypti_expert_classification_count']:
                                classification['is_albopictus'] = True
                                classification['score'] = status['albopictus_expert_classification_score']
                                #return status['albopictus_expert_classification_score']
                            else:
                                classification['is_aegypti'] = True
                                classification['score'] = status['aegypti_expert_classification_score']
                                #return status['aegypti_expert_classification_score']

                    elif albopictus_score <= 0 and aegypti_score > 0: #conflict -> Some experts reasonably sure is aegypti, some think is neither or none
                        if albopictus_score == -3:
                            classification['is_aegypti'] = True
                            classification['score'] = status['aegypti_expert_classification_score']
                            #return status['aegypti_expert_classification_score']
                        else:
                            if status['albopictus_expert_classification_count'] > status['aegypti_expert_classification_count']:
                                classification['is_albopictus'] = True
                                classification['score'] = status['albopictus_expert_classification_score']
                                #return status['albopictus_expert_classification_score']
                            else:
                                classification['is_aegypti'] = True
                                classification['score'] = status['aegypti_expert_classification_score']
                                #return status['aegypti_expert_classification_score']
                    elif albopictus_score <= 0 and aegypti_score <= 0:
                        #Case 1A, 1B, -2 -> Counts as albo -0.5, aegy -0.5
                        if status['albopictus_expert_classification_count'] == status['aegypti_expert_classification_count'] and status['albopictus_expert_classification_count'] != 3 and status['aegypti_expert_classification_count'] != 3:
                            if status['aegypti_expert_classification_score'] == status['albopictus_expert_classification_score']:
                                classification['is_none'] = True
                                classification['score'] = albopictus_score
                            else:
                                classification['conflict'] = True
                                classification['score'] = -4
                        elif status['albopictus_expert_classification_count'] > status['aegypti_expert_classification_count']:
                            classification['is_albopictus'] = True
                            classification['score'] = status['albopictus_expert_classification_score']
                        elif status['albopictus_expert_classification_count'] < status['aegypti_expert_classification_count']:
                            classification['is_aegypti'] = True
                            classification['score'] = status['aegypti_expert_classification_score']
                        else:
                            classification['is_none'] = True
                            classification['score'] = albopictus_score
                        #return albopictus_score
        #unreachable, in theory - left here for security purposes
        return classification

    def get_mean_expert_site_score(self):
        sum_scores = 0
        mean_score = -3
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, site_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, site_certainty_category__isnull=False).count() == 0:
            return -3
        super_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exclude(site_certainty_category__isnull=True).values_list('site_certainty_category', flat=True)
        if super_scores:
            for this_score in super_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores / float(super_scores.count())
            return mean_score
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, site_certainty_category__isnull=True).count() > 0 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, site_certainty_category__isnull=False).count() == 0:
            return -3
        expert_scores = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).exclude(site_certainty_category__isnull=True).values_list('site_certainty_category', flat=True)
        if expert_scores:
            for this_score in expert_scores:
                if this_score:
                    sum_scores += this_score
            mean_score = sum_scores/float(expert_scores.count())
        return mean_score

    def get_final_combined_expert_score(self):
        score = -3
        if self.type == self.TYPE_SITE:
            score = self.get_mean_expert_site_score()
        elif self.type == self.TYPE_ADULT:
            classification = self.get_mean_combined_expert_adult_score()
            score = classification['score']
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_score(self):
        score = -3
        if self.type == self.TYPE_SITE:
            score = self.get_mean_expert_site_score()
        elif self.type == self.TYPE_ADULT:
            score = self.get_mean_expert_adult_score()
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_score_aegypti(self):
        score = -3
        if self.type == self.TYPE_SITE:
            score = self.get_mean_expert_site_score()
        elif self.type == self.TYPE_ADULT:
            score = self.get_mean_expert_adult_score_aegypti()
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_status(self):
        finished_annotations = self.expert_report_annotations.filter(validation_complete=True)

        super_expert_annotations = finished_annotations.filter(user__groups__name='superexpert', revise=True)
        super_expert_status = super_expert_annotations.aggregate(min_status=models.Min('status'))

        if super_expert_status['min_status'] is not None:
            return super_expert_status['min_status']

        expert_status = finished_annotations.filter(user__groups__name='expert').aggregate(min_status=models.Min('status'))
        if expert_status['min_status'] is not None:
            return expert_status['min_status']

        return 1

    def get_final_expert_status_text(self):
        return dict(STATUS_CATEGORIES)[self.get_final_expert_status()]

    def get_final_expert_status_bootstrap(self):
        result = '<span data-toggle="tooltip" data-placement="bottom" title="' + self.get_final_expert_status_text() + '" class="' + ('glyphicon glyphicon-eye-open' if self.get_final_expert_status() == 1 else ('glyphicon glyphicon-flag' if self.get_final_expert_status() == 0 else 'glyphicon glyphicon-eye-close')) + '"></span>'
        return result

    def get_is_expert_validated(self):
        return ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).count() >= 3

    def get_tags_bootstrap_superexpert(self):
        result = ''
        s = set()
        for ano in self.expert_report_annotations.all():
            tags = ano.tags.all()
            for tag in tags:
                if not tag in s:
                    s.add(tag)
                    result += '<span class="label label-success" data-toggle="tooltip" title="tagged by ' + ano.user.username + '" data-placement="bottom">' + (
                        tag.name) + '</span>'
        if (len(s) == 0):
            return '<span class="label label-default" data-toggle="tooltip" data-placement="bottom" title="tagged by no one">No tags</span>'
        return result

    def get_tags_bootstrap(self):
        result = ''
        s = set()
        for ano in self.expert_report_annotations.all():
            tags = ano.tags.all()
            for tag in tags:
                if not tag in s:
                    s.add(tag)
                    result += '<span class="label label-success" data-toggle="tooltip" title="tagged by someone" data-placement="bottom">' + (tag.name) + '</span>'
        if (len(s) == 0):
            return '<span class="label label-default" data-toggle="tooltip" data-placement="bottom" title="tagged by no one">No tags</span>'
        return result

    def get_single_report_view_link(self):
        result = reverse('single_report_view', kwargs={"version_uuid": self.version_UUID})
        return result

    def get_who_has(self):
        result = []
        for ano in self.expert_report_annotations.all().select_related('user'):
            result.append(
                ano.user.username + (': validated' if ano.validation_complete else ': pending')
            )

        return ", ".join(result)

    def get_expert_has_been_assigned_long_validation(self):
        for ano in self.expert_report_annotations.all().select_related('user'):
            if not ano.user.userstat.is_superexpert():
                if ano.simplified_annotation == False:
                    return True
        return False

    def get_who_has_count(self):
        return self.expert_report_annotations.all().count()

    def get_expert_recipients(self):
        result = []
        for ano in self.expert_report_annotations.all().select_related('user'):
            if not ano.user.userstat.is_superexpert():
                result.append(ano.user.username)
        return '+'.join(result)

    def get_superexpert_completed_recipients(self):
        result = []
        for ano in self.expert_report_annotations.all().select_related('user'):
            if ano.validation_complete and ano.user.userstat.is_superexpert():
                result.append(ano.user.username)
        return '+'.join(result)

    def get_expert_recipients_names(self):
        result = []

        for ano in self.expert_report_annotations.all().select_related('user'):
            if not ano.user.userstat.is_superexpert():
                if ano.user.first_name and ano.user.last_name:
                    result.append(ano.user.first_name + ' ' + ano.user.last_name)
                else:
                    result.append(ano.user.username)
        return '+'.join(result)

    def get_who_has_bootstrap(self):
        result = []
        for ano in self.expert_report_annotations.all().select_related("user"):
            result.append(
                '<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by ' + ano.user.username) if ano.validation_complete else ('pending with ' + ano.user.username)) + '">' + ano.user.username + ' <span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>'
            )
        return ' '.join(result)

    def get_final_photo_url_for_notification(self):
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists():
            super_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if super_photos:
                winning_photo_id = Counter(super_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id).get_medium_url()
            return None
        else:
            expert_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if expert_photos:
                winning_photo_id = Counter(expert_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id).get_medium_url()
            else:
                if self.get_first_visible_photo() is not None:
                    return self.get_first_visible_photo().get_medium_url()
            return None

    def get_first_visible_photo(self):
        return self.visible_photos.first()

    def get_final_photo_html(self):
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists():
            super_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if super_photos.count() > 0:
                winning_photo_id = Counter(super_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id)
            else:
                expert_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True,best_photo__isnull=False).values_list('best_photo', flat=True)
                if expert_photos.count() > 0:
                    winning_photo_id = Counter(expert_photos).most_common()[0][0]
                    if winning_photo_id:
                        winning_photo = Photo.objects.filter(pk=winning_photo_id)
                        if winning_photo and winning_photo.count() > 0:
                            return Photo.objects.get(pk=winning_photo_id)
                else:
                    photos = self.visible_photos.order_by('-id')
                    if photos and len(photos) > 0:
                        return photos[0]
            return None
        else:
            expert_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if expert_photos.count() > 0:
                winning_photo_id = Counter(expert_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id)
            else:
                photos = self.visible_photos.order_by('-id')
                if photos and len(photos) > 0:
                    return photos[0]
            return None

    def get_final_public_note(self):
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists():
            super_notes = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exclude(edited_user_notes='').values_list('edited_user_notes', flat=True)
            if super_notes:
                winning_note = Counter(super_notes).most_common()[0][0]
                if winning_note:
                    return winning_note
            return None
        else:
            expert_notes = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).exclude(edited_user_notes='').values_list('edited_user_notes', flat=True)
            if expert_notes:
                winning_note = Counter(expert_notes).most_common()[0][0]
                if winning_note:
                    return winning_note
            return None

    def get_final_note_to_user_html(self):
        notes = None
        super_notes = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exclude(message_for_user='').values_list('message_for_user', flat=True)
        if super_notes:
            notes = super_notes
        else:
            expert_notes = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).exclude(message_for_user='').values_list('message_for_user', flat=True)
            if expert_notes:
                notes = expert_notes
        if notes:
            n = len(notes)
            if n == 1:
                return '<strong>Message from Expert:</strong> ' + notes[0]
            elif n > 1:
                result = ''
                i = 1
                for note in notes:
                    result += '<strong>Message from Expert ' + str(i) + ':</strong> ' + note
                    if i < n:
                        result += '<br>'
                return result
        else:
            return ''


def one_day_between_and_same_week(r1_date_less_recent, r2_date_most_recent):
    day_before = r2_date_most_recent - timedelta(days=1)
    week_less_recent = r1_date_less_recent.isocalendar()[1]
    week_most_recent = r2_date_most_recent.isocalendar()[1]
    return day_before.year == r1_date_less_recent.year and day_before.month == r1_date_less_recent.month and day_before.day == r1_date_less_recent.day and week_less_recent == week_most_recent


def get_user_reports_count(user):
    user_uuids = []
    if user.profile:
        ps = user.profile.profile_devices.all()
        for p in ps:
            user_uuids.append(p.user_UUID)
    else:
        user_uuids.append(user.user_UUID)
    reports = Report.objects.filter(user__user_UUID__in=user_uuids).exclude(type=Report.TYPE_BITE)
    last_versions = filter(lambda x: not x.deleted and x.latest_version, reports)
    return len(list(last_versions))


def package_number_allows_notification(report):
    minimum_package_version = getattr(conf, 'MINIMUM_PACKAGE_VERSION_SCORING_NOTIFICATIONS', 32)
    if report is not None:
        if report.package_version is not None:
            if report.package_version >= minimum_package_version:
                return True
    return False


def issue_notification(report, reason_label, xp_amount, current_domain):
    if getattr( conf, 'DISABLE_ACHIEVEMENT_NOTIFICATIONS', True) == False:
        if package_number_allows_notification(report):
            #table = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}
            notification_content = NotificationContent()
            # context_es = {}
            # context_ca = {}
            context_en = {}
            context_native = {}
            # locale_for_en = get_locale_for_en(report)
            locale_for_native = get_locale_for_native(report)
            notification_content.native_locale = locale_for_native
            super_movelab = User.objects.get(pk=24)
            # notification_content.title_es = "¡Acabas de recibir una recompensa de puntos!"
            # notification_content.title_ca = "Acabes de rebre una recompensa de punts!"
            notification_content.title_en = get_translation_in("you_just_received_a_points_award",'en')
            notification_content.title_native = get_translation_in("you_just_received_a_points_award", locale_for_native)
            if report is not None:
                if report.get_final_photo_url_for_notification():
                    #context_es['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                    context_en['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                    context_native['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                    #context_ca['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                else:
                    pic = report.get_first_visible_photo()
                    if pic:
                        pic_url = pic.get_medium_url()
                        if pic_url is not None:
                            # context_es['picture_link'] = 'http://' + current_domain + pic_url
                            context_en['picture_link'] = 'http://' + current_domain + pic_url
                            context_native['picture_link'] = 'http://' + current_domain + pic_url
                            # context_ca['picture_link'] = 'http://' + current_domain + pic_url

            # context_es['amount_awarded'] = xp_amount
            context_en['amount_awarded'] = xp_amount
            context_native['amount_awarded'] = xp_amount
            # context_ca['amount_awarded'] = xp_amount

            # context_es['reason_awarded'] = get_translation_in(reason_label, 'es')
            context_en['reason_awarded'] = get_translation_in(reason_label, 'en')
            context_native['reason_awarded'] = get_translation_in(reason_label, locale_for_native)
            # context_ca['reason_awarded'] = get_translation_in(reason_label, 'ca')

            #notification_content.body_html_es = render_to_string('tigaserver_app/award_notification_es.html', context_es)
            #notification_content.body_html_ca = render_to_string('tigaserver_app/award_notification_ca.html', context_ca)
            notification_content.body_html_en = render_to_string('tigaserver_app/award_notification_en.html', context_en)
            try:
                notification_content.body_html_native = render_to_string('tigaserver_app/award_notification_' + locale_for_native + '.html', context_native)
            except TemplateDoesNotExist:
                notification_content.body_html_native = render_to_string('tigaserver_app/award_notification_en.html',context_en)


            #notification_content.body_html_es = notification_content.body_html_es.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')
            #notification_content.body_html_ca = notification_content.body_html_ca.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')
            notification_content.body_html_en = notification_content.body_html_en.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')
            notification_content.body_html_native = notification_content.body_html_native.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')


            '''
            if conf.DEBUG == True:
                print(notification_content.body_html_es)
                print(notification_content.body_html_ca)
                print(notification_content.body_html_en)
            '''
            notification_content.save()
            notification = Notification(report=report, expert=super_movelab, notification_content=notification_content)
            notification.save()
            notification.send_to_user(user=report.user)

@receiver(post_save, sender=Report)
def maybe_give_awards(sender, instance, created, **kwargs):
    #only for adults and sites
    if created:
        try:
            profile_uuids = None
            if instance.user.profile is not None:
                profile_uuids = TigaUser.objects.filter(profile=instance.user.profile).values('user_UUID')
            super_movelab = User.objects.get(pk=24)
            n_reports = get_user_reports_count(instance.user)
            if n_reports == 10:
                grant_10_reports_achievement(instance, super_movelab)
                issue_notification(instance, ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP, conf.HOST_NAME)
            if n_reports == 20:
                grant_20_reports_achievement(instance, super_movelab)
                issue_notification(instance, ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP, conf.HOST_NAME)
            if n_reports == 50:
                grant_50_reports_achievement(instance, super_movelab)
                issue_notification(instance, ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP, conf.HOST_NAME)
            if instance.type == Report.TYPE_ADULT or instance.type == Report.TYPE_SITE:
                # check award for first of season
                current_year = instance.creation_time.year
                if profile_uuids is None:
                    awards = Award.objects.filter(given_to=instance.user).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season')
                else:
                    awards = Award.objects.filter(given_to__user_UUID__in=profile_uuids).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season')
                if awards.count() == 0:  # not yet awarded
                    # can be first of season?
                    if instance.creation_time.month >= conf.SEASON_START_MONTH and instance.creation_time.day >= conf.SEASON_START_DAY:
                        grant_first_of_season(instance, super_movelab)
                        issue_notification(instance, START_OF_SEASON, get_xp_value_of_category(START_OF_SEASON), conf.HOST_NAME)
                else: #it already has been awarded. If this report is last version of originally awarded, transfer award to last version
                    if instance.latest_version: #this report is the last version
                        version_of_previous = instance.version_number - 1
                        if awards.filter(report__version_number=version_of_previous).exists(): #was previous version awarded with first of season?
                            #if yes, transfer award to current version
                            award = awards.filter(report__version_number=version_of_previous).first()
                            award.report = instance
                            award.save()

                report_day = instance.creation_time.day
                report_month = instance.creation_time.month
                report_year = instance.creation_time.year
                if profile_uuids is None:
                    awards = Award.objects \
                        .filter(report__creation_time__year=report_year) \
                        .filter(report__creation_time__month=report_month) \
                        .filter(report__creation_time__day=report_day) \
                        .filter(report__user=instance.user) \
                        .filter(category__category_label='daily_participation').order_by(
                        'report__creation_time')  # first is oldest
                else:
                    awards = Award.objects \
                        .filter(report__creation_time__year=report_year) \
                        .filter(report__creation_time__month=report_month) \
                        .filter(report__creation_time__day=report_day) \
                        .filter(report__user__user_UUID__in=profile_uuids) \
                        .filter(category__category_label='daily_participation').order_by(
                        'report__creation_time')  # first is oldest
                if awards.count() == 0: # not yet awarded
                    grant_first_of_day(instance, super_movelab)
                    issue_notification(instance, DAILY_PARTICIPATION, get_xp_value_of_category(DAILY_PARTICIPATION), conf.HOST_NAME)

                date_1_day_before_report = instance.creation_time - timedelta(days=1)
                date_1_day_before_report_adjusted = date_1_day_before_report.replace(hour=23, minute=59, second=59)
                if profile_uuids is None:
                    report_before_this_one = Report.objects.filter(user=instance.user).filter(creation_time__lte=date_1_day_before_report_adjusted).order_by('-creation_time').first()  # first is most recent
                else:
                    report_before_this_one = Report.objects.filter(user__user_UUID__in=profile_uuids).filter(creation_time__lte=date_1_day_before_report_adjusted).order_by('-creation_time').first()  # first is most recent
                if report_before_this_one is not None and one_day_between_and_same_week(report_before_this_one.creation_time, instance.creation_time):
                    #report before this one has not been awarded neither 2nd nor 3rd day streak
                    if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count()==0 and Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_3').count()==0:
                        grant_two_consecutive_days_sending(instance, super_movelab)
                        issue_notification(instance, FIDELITY_DAY_2, get_xp_value_of_category(FIDELITY_DAY_2), conf.HOST_NAME)
                    else:
                        if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count() == 1:
                            grant_three_consecutive_days_sending(instance, super_movelab)
                            issue_notification(instance, FIDELITY_DAY_3, get_xp_value_of_category(FIDELITY_DAY_3), conf.HOST_NAME)
        except User.DoesNotExist:
            pass


class ReportResponse(models.Model):
    report = models.ForeignKey(Report, related_name='responses', help_text='Report to which this response is associated.', on_delete=models.CASCADE, )
    question_id = models.IntegerField(blank=True, null=True, help_text='Numeric identifier of the question.')
    question = models.CharField(max_length=1000, help_text='Question that the user responded to.')
    answer_id = models.IntegerField(blank=True, null=True, help_text='Numeric identifier of the answer.')
    answer = models.CharField(max_length=1000, help_text='Answer that user selected.')
    answer_value = models.CharField(max_length=1000, blank=True, null=True, help_text='The value right now can contain 2 things: an integer representing the number or bites, or either a WKT representation of a point for a location answer. In all other cases, it will be blank')

    def __unicode__(self):
        return str(self.id)

@deconstructible
class MakeImageUUID(object):
    path = ''

    def __init__(self, path):
        self.path = path

    def __call__(self,instance,filename):
        extension = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), extension)
        return os.path.join(self.path, filename)

make_image_uuid = MakeImageUUID('tigapics')

'''
def make_image_uuid(path):
    def wrapper(instance, filename):
        extension = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), extension)
        return os.path.join(path, filename)
    return wrapper
'''

def make_uuid():
    return str(uuid.uuid4())


BLOOD_GENRE = (('male', 'Male'), ('female', 'Female'), ('fblood', 'Female blood'), ('fgravid', 'Female gravid'), ('fgblood', 'Female gravid + blood'), ('dk', 'Dont know') )

class Photo(models.Model):
    """
    Photo uploaded by user.
    """
    photo = models.ImageField(upload_to=make_image_uuid, help_text='Photo uploaded by user.')
    report = models.ForeignKey(Report, related_name='photos', help_text='Report and version to which this photo is associated (36-digit '
                                                 'report_UUID).', on_delete=models.CASCADE, )
    hide = models.BooleanField(default=False, help_text='Hide this photo from public views?')
    uuid = models.CharField(max_length=36, default=make_uuid)
    blood_genre = models.CharField(max_length=20, choices=BLOOD_GENRE, null=True, default=None)

    def __unicode__(self):
        return self.photo.name

    def get_user(self):
        return self.report.user

    def get_date(self):
        return self.report.version_time.strftime("%d-%m-%Y %H:%M")

    def get_small_path(self):
        return self.photo.path.replace('tigapics/', 'tigapics_small/')

    def get_popup_path(self):
        return self.photo.path.replace('tigapics/', 'tigapics_popups/')

    def get_small_url(self):
        if os.path.isfile(self.photo.path):
            if not os.path.isfile(self.get_small_path()):
                try:
                    im = Image.open(self.photo.path)
                    try:
                        im.thumbnail((120, 120), Image.ANTIALIAS)
                    except IOError:
                        im.thumbnail((120, 120), Image.NEAREST)
                    im.save(self.get_small_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_small/')

    def get_popup_url(self):
        if os.path.isfile(self.photo.path):
            if not os.path.isfile(self.get_popup_path()):
                try:
                    im = Image.open(self.photo.path)
                    try:
                        im.thumbnail((180, 180), Image.ANTIALIAS)
                    except IOError:
                        im.thumbnail((180, 180), Image.NEAREST)
                    im.save(self.get_popup_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_popups/')

    def small_image_(self):
        return '<a href="{0}"><img src="{1}"></a>'.format(self.photo.url, self.get_small_url())

    small_image_.allow_tags = True

    def popup_image(self):
        return '<a href="{0}" target="_blank"><img src="{1}"></a>'.format(self.photo.url, self.get_popup_url())

    popup_image.allow_tags = True

    def get_medium_path(self):
        return self.photo.path.replace('tigapics/', 'tigapics_medium/')

    def get_medium_url(self):
        if os.path.isfile(self.photo.path):
            if not os.path.isfile(self.get_medium_path()):
                try:
                    im = Image.open(self.photo.path)
                    try:
                        im.thumbnail((460, 460), Image.ANTIALIAS)
                    except IOError:
                        im.thumbnail((460, 460), Image.NEAREST)
                    im.save(self.get_medium_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_medium/')

    def medium_image_(self):
        return '<a href="{0}"><img src="{1}"></a>'.format(self.photo.url, self.get_medium_url())

    def medium_image_for_validation_(self):
        return '<a target="_blank" href="{0}"><img src="{1}"></a>'.format(self.photo.url, self.get_medium_url())

    # Metadata scrubbing
    # def save(self, *args, **kwargs):
    #     image = Image.open(self.photo)
    #     photo_name = self.photo.name
    #     data = list(image.getdata())
    #     scrubbed_image = Image.new(image.mode, image.size)
    #     scrubbed_image.putdata(data)
    #     scrubbed_image_io = BytesIO()
    #     scrubbed_image.save(scrubbed_image_io,"JPEG")
    #     self.photo = File(scrubbed_image_io, name=photo_name)
    #     super(Photo, self).save(*args, **kwargs)


    medium_image_.allow_tags = True

    user = property(get_user)
    date = property(get_date)


class Fix(TimeZoneModelMixin, models.Model):
    """
    Location fix uploaded by user.
    """
    user_coverage_uuid = models.CharField(blank=True, null=True, max_length=36, help_text='UUID randomly generated on '
                                                                            'phone to identify each unique user, '
                                                                            'but only within the coverage data so '
                                                                            'that privacy issues are not raised by '
                                                                            'linking this to the report data.'
                                                                            '. Must be exactly 36 '
                                                                            'characters (32 hex digits plus 4 hyphens).')

    fix_time = models.DateTimeField(help_text='Date and time when fix was recorded on phone. Format as ECMA '
                                              '262 date time string (e.g. "2014-05-17T12:34:56'
                                              '.123+01:00".')
    server_upload_time = models.DateTimeField(auto_now_add=True, help_text='Date and time registered by server when '
                                                                           'it received fix upload. Automatically '
                                                                           'generated by server.')
    phone_upload_time = models.DateTimeField(help_text='Date and time on phone when it uploaded fix. Format '
                                                       'as ECMA '
                                                       '262 date time string (e.g. "2014-05-17T12:34:56'
                                                       '.123+01:00".')
    masked_lon = models.FloatField(help_text='Longitude rounded down to nearest 0.5 decimal degree (floor(lon/.5)*.5)'
                                             '.')
    masked_lat = models.FloatField(help_text='Latitude rounded down to nearest 0.5 decimal degree (floor(lat/.5)*.5).')
    mask_size = models.FloatField(null=True, blank=True, help_text='size of location mask used')
    power = models.FloatField(null=True, blank=True, help_text='Power level of phone at time fix recorded, '
                                                               'expressed as proportion of full charge. Range: 0-1.')

    def __unicode__(self):
        result = 'NA'
        if self.user_coverage_uuid is not None:
            result = self.user_coverage_uuid
        return result

    # See TimeZoneModelMixin
    def _get_latitude_for_timezone(self):
        return self.masked_lat

    def _get_longitude_for_timezone(self):
        return self.masked_lon


    class Meta:
        verbose_name = "fix"
        verbose_name_plural = "fixes"


class Configuration(models.Model):
    id = models.AutoField(primary_key=True, help_text='Auto-incremented primary key record ID.')
    samples_per_day = models.IntegerField(help_text="Number of randomly-timed location samples to take per day.")
    creation_time = models.DateTimeField(help_text='Date and time when this configuration was created by MoveLab. '
                                                   'Automatically generated when record is saved.',
                                         auto_now_add=True)

    def __unicode__(self):
        return str(self.samples_per_day)


class CoverageArea(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()
    n_fixes = models.PositiveIntegerField()
    last_modified = models.DateTimeField(auto_now=True)
    latest_report_server_upload_time = models.DateTimeField()
    latest_fix_id = models.PositiveIntegerField()

    def __unicode__(self):
        return str(self.id)

    class Meta:
        unique_together = ("lat", "lon")


class CoverageAreaMonth(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()
    year = models.IntegerField()
    month = models.IntegerField()
    n_fixes = models.PositiveIntegerField()
    last_modified = models.DateTimeField(auto_now=True)
    latest_report_server_upload_time = models.DateTimeField()
    latest_fix_id = models.PositiveIntegerField()

    def __unicode__(self):
        return str(self.id)

    class Meta:
        unique_together = ("lat", "lon", "year", "month")

class NotificationContent(models.Model):
    body_html_es = models.TextField(default=None, blank=True, null=True, help_text='Expert comment, expanded and allows html, in spanish')
    body_html_ca = models.TextField(default=None, blank=True, null=True, help_text='Expert comment, expanded and allows html, in catalan')
    body_html_en = models.TextField(default=None, blank=True, null=True, help_text='Expert comment, expanded and allows html, in english')
    title_es = models.TextField(default=None, blank=True, null=True, help_text='Title of the comment, shown in non-detail view, in spanish')
    title_ca = models.TextField(default=None, blank=True, null=True, help_text='Title of the comment, shown in non-detail view, in catalan')
    title_en = models.TextField(default=None, blank=True, null=True, help_text='Title of the comment, shown in non-detail view, in english')
    predefined_available_to = models.ForeignKey(User, blank=True, null=True, related_name="predefined_notifications", help_text='If this field is not null, this notification is predefined - the predefined map notifications will go here. This field indicates the expert to which the notification is available', on_delete=models.SET_NULL, )
    body_html_native = models.TextField(default=None,blank=True,null=True, help_text='Expert comment, expanded and allows html, in the language indicated by the field native_locale')
    title_native = models.TextField(default=None, blank=True, null=True, help_text='Title of the comment, shown in non-detail view, in the language indicated by the field title_native')
    native_locale = models.CharField(default=None, blank=True, null=True, max_length=10, help_text='Locale code for text in body_html_native and title_native')
    notification_label = models.CharField(default=None, blank=True, null=True, max_length=255, help_text='Arbitrary label used to group thematically equal notifications. Optional. ')

    @property
    def body_image(self) -> Optional[str]:
        soup = BeautifulSoup(self.body_html_en, 'html.parser')

        img_tag = soup.find('img')
        if img_tag:
            return img_tag.get('src')

        return None

    def _get_localized_field(self, fieldname_prefix: str, language_code: Optional[str] = None) -> str:
        # Default to english
        language_code = language_code or 'en'

        if self.native_locale and self.native_locale.lower().strip() == language_code.lower().strip():
            language_code = 'native'

        # Check if the field for the specified language exists
        result_en = getattr(self, f"{fieldname_prefix}_en")
        result_local = None
        fieldname = f"{fieldname_prefix}_{language_code}"
        if hasattr(self, fieldname):
            result_local = getattr(self, fieldname)

        # Return result with fallback to English
        return result_local or result_en

    def get_title(self, language_code: Optional[str] = None) -> str:
        return self._get_localized_field(fieldname_prefix='title', language_code=language_code)

    def get_body_html(self, language_code: Optional[str] = None) -> str:
        return self._get_localized_field(fieldname_prefix='body_html', language_code=language_code)

    def get_body(self, language_code: Optional[str] = None) -> str:
        body_html = self.get_body_html(language_code=language_code)
        soup = BeautifulSoup(body_html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)

class Notification(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', null=True, blank=True, related_name='report_notifications', help_text='Report regarding the current notification', on_delete=models.CASCADE, )
    # The field 'user' is kept for backwards compatibility with the map notifications. It only has meaningful content on MAP NOTIFICATIONS
    # and in all other cases is given a default value (null user 00000000-0000-0000-0000-000000000000)
    user = models.ForeignKey(TigaUser, default='00000000-0000-0000-0000-000000000000', related_name="user_notifications", help_text='User to which the notification will be sent', on_delete=models.CASCADE, )
    expert = models.ForeignKey(User, null=True, blank=True, related_name="expert_notifications", help_text='Expert sending the notification', on_delete=models.SET_NULL, )
    date_comment = models.DateTimeField(auto_now_add=True)
    #blank is True to avoid problems in the migration, this should be removed!!
    notification_content = models.ForeignKey(NotificationContent,blank=True, null=True,related_name="notification_content",help_text='Multi language content of the notification', on_delete=models.SET_NULL, )
    #All this becomes obsolete, now all notification text is outside. This allows for re-use in massive notifications
    expert_comment = models.TextField('Expert comment', help_text='Text message sent to user')
    expert_html = models.TextField('Expert comment, expanded and allows html', help_text='Expanded message information goes here. This field can contain HTML')
    photo_url = models.TextField('Url to picture that originated the comment', null=True, blank=True, help_text='Relative url to the public report photo')
    public = models.BooleanField(default=False, help_text='Whether the notification is shown in the public map or not')
    # The field 'acknowledged' is kept for backwards compatibility with the map notifications. It only has meaningful content on MAP NOTIFICATIONS
    acknowledged = models.BooleanField(default=False, help_text='This is set to True through the public API, when the user signals that the message has been received')
    # map_notification = models.BooleanField(default=False, help_text='Flag field to help discriminate notifications which have been issued from the map')


    def send_to_topic(self, topic: 'NotificationTopic', push: bool = True, language_code: Optional[str] = None) -> Optional[str]:
        obj, _ = SentNotification.objects.get_or_create(
            sent_to_topic=topic,
            notification=self
        )

        if push:
            return obj.send_push(language_code=language_code)

    def send_to_user(self, user: TigaUser, push: bool = True) -> Optional[str]:
        obj, _ = SentNotification.objects.get_or_create(
            sent_to_user=user,
            notification=self
        )

        if push:
            return obj.send_push(language_code=user.language_iso2)

class AcknowledgedNotification(models.Model):
    user = models.ForeignKey(TigaUser, related_name="user_acknowledgements",help_text='User which has acknowledged the notification', on_delete=models.CASCADE, )
    notification = models.ForeignKey(Notification, related_name="notification_acknowledgements",help_text='The notification which has been acknowledged or not', on_delete=models.CASCADE, )
    # no explicit ack field. If there is a row in this table, it has been acked
    #acknowledged = models.BooleanField(default=True, help_text='This is set to True through the public API, when the user signals that the message has been received')

    class Meta:
        unique_together = ( 'user', 'notification', )


TOPIC_GROUPS = ((0, 'General'), (1, 'Language topics'), (2, 'Country topics'), (3, 'Country nuts3'), (4, 'Country nuts2'), (5, 'Special'))


class NotificationTopic(models.Model):
    topic_code = models.CharField(max_length=100, unique=True, help_text='Code for the topic.')
    topic_description = models.TextField(help_text='Description for the topic, in english.')
    topic_group = models.IntegerField('Group of topics', choices=TOPIC_GROUPS, default=0, help_text='Your degree of belief that at least one photo shows a tiger mosquito breeding site')


class UserSubscription(models.Model):
    user = models.ForeignKey(TigaUser, related_name="user_subscriptions", help_text='User which is subscribed to the topic', on_delete=models.CASCADE, )
    topic = models.ForeignKey(NotificationTopic, related_name="topic_users", help_text='Topics to which the user is subscribed', on_delete=models.CASCADE, )

    def save(self, *args, **kwargs):
        if self.user.device_token:
            try:
                firebase_admin.messaging.subscribe_to_topic(
                    tokens=[self.user.device_token,],
                    topic=self.topic.topic_code
                )
            except (FirebaseError, ValueError) as e:
                logger_notification.exception(str(e))

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.user.device_token:
            try:
                firebase_admin.messaging.unsubscribe_from_topic(
                    tokens=[self.user.device_token,],
                    topic=self.topic.topic_code
                )
            except (FirebaseError, ValueError) as e:
                logger_notification.exception(str(e))

        return super().delete(*args, **kwargs)

    class Meta:
        unique_together = ( 'user', 'topic', )


class SentNotification(models.Model):
    sent_to_user = models.ForeignKey(TigaUser, null=True, blank=True, related_name="user_sentnotifications", help_text='User to which the notification was sent', on_delete=models.CASCADE, )
    sent_to_topic = models.ForeignKey(NotificationTopic, null=True, blank=True, related_name="topic_sentnotifications", help_text='Topic to which the notification was sent.', on_delete=models.CASCADE, )
    #both sent_to_user and sent_to_topic can be null, but they can't be null at the same time. In other words, a sending
    #you either send a notification to a user, or to a group of users via topics
    notification = models.ForeignKey(Notification, related_name="notification_sendings", help_text='The notification which has been sent', on_delete=models.CASCADE, )

    def send_push(self, language_code: str = None):

        if settings.DISABLE_PUSH:
            return

        # See: https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging
        # See: https://firebaseopensource.com/projects/flutter/plugins/packages/firebase_messaging/readme/
        message_payload = dict(
            data={
                "id": str(self.notification.pk)
            },
            notification=FirebaseNotification(
                title=self.notification.notification_content.get_title(language_code=language_code),
                body=self.notification.notification_content.get_body(language_code=language_code),
                image=self.notification.notification_content.body_image
            ),
            android=AndroidConfig(
                notification=AndroidNotification(
                    click_action='FLUTTER_NOTIFICATION_CLICK'
                )
            )
        )
        message_id = None
        if self.sent_to_topic:
            try:
                message_id = firebase_admin.messaging.send(
                    message=Message(
                        **message_payload,
                        topic=self.sent_to_topic.topic_code
                    ),
                    dry_run=settings.DRY_RUN_PUSH,
                )
            except firebase_admin._messaging_utils.UnregisteredError:
                logger_notification.exception(f"Topic {self.sent_to_topic.topic_code} not valid")
            except (FirebaseError, ValueError) as e:
                logger_notification.exception(str(e))
            except Exception as e:
                logger_notification.exception(str(e))
        elif self.sent_to_user and self.sent_to_user.device_token:
            try:
                message_id = firebase_admin.messaging.send(
                    message=Message(
                        **message_payload,
                        token=self.sent_to_user.device_token
                    ),
                    dry_run=settings.DRY_RUN_PUSH,
                )
            except firebase_admin._messaging_utils.UnregisteredError:
                logger_notification.exception(f"Device token {self.sent_to_user.device_token} not valid")
            except (FirebaseError, ValueError) as e:
                logger_notification.exception(str(e))
            except Exception as e:
                logger_notification.exception(str(e))

        return message_id


class AwardCategory(models.Model):
    category_label = models.TextField(help_text='Coded label for the translated version of the award. For instance award_good_picture. This code refers to strings in several languages')
    xp_points = models.IntegerField(help_text='Number of xp points associated to this kind of award')
    category_long_description = models.TextField(default=None, blank=True, null=True, help_text='Long description specifying conditions in which the award should be conceded')


class Award(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', default=None, blank=True, null=True, related_name='report_award', help_text='Report which the award refers to. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    date_given = models.DateTimeField(default=datetime.now, help_text='Date in which the award was given')
    given_to = models.ForeignKey(TigaUser, blank=True, null=True, related_name="user_awards", help_text='User to which the notification was awarded. Usually this is the user that uploaded the report, but the report can be blank for special awards', on_delete=models.CASCADE, )
    expert = models.ForeignKey(User, null=True, blank=True, related_name="expert_awards", help_text='Expert that gave the award', on_delete=models.SET_NULL, )
    category = models.ForeignKey(AwardCategory, blank=True, null=True, related_name="category_awards", help_text='Category to which the award belongs. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    special_award_text = models.TextField(default=None, blank=True, null=True, help_text='Custom text for custom award')
    special_award_xp = models.IntegerField(default=0, blank=True, null=True, help_text='Custom xp awarded')

    def __str__(self):
        if self.category:
            return str(self.category.category_label)
        else:
            return self.special_award_text


class OWCampaigns(models.Model):
    """
    This model contains the information about Overwintering campaigns. Each campaign takes place in a given country,
    over a period of time. In a given country at a given period, only one campaign can be active.
    """
    country = models.ForeignKey('tigaserver_app.EuropeCountry', related_name="campaigns", help_text='Country in which the campaign is taking place', on_delete=models.PROTECT, )
    posting_address = models.TextField(help_text='Full posting address of the place where the samples will be sent')
    campaign_start_date = models.DateTimeField(help_text='Date when the campaign starts. No samples should be collected BEFORE this date.')
    campaign_end_date = models.DateTimeField(help_text='Date when the campaign ends. No samples should be collected AFTER this date.')


class OrganizationPin(models.Model):
    """
    This model is queryable via API, it's meant to represent a list of organizations with a geographical location.
    Each of these organizations has a link to a web page with the detailed information. The text in textual_description
    should be shown in a pin dialog in a map
    """
    point = models.PointField(srid=4326)
    textual_description = models.TextField(help_text='Text desription on the pin. This text is meant to be visualized as the text body of the dialog on the map')
    page_url = models.URLField(help_text='URL link to the organization page')


class IAScore(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', related_name='report_iascore', help_text='Report which the score refers to.', on_delete=models.CASCADE, )
    photo = models.ForeignKey('tigaserver_app.Photo', related_name='photo_iascore', help_text='Photo to which the score refers to', on_delete=models.CASCADE, )
    f1_c1 = models.FloatField(blank=True, null=True, help_text='Score for filter 1, class 1')
    f1_c2 = models.FloatField(blank=True, null=True, help_text='Score for filter 1, class 2')
    f2_c1 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 1')
    f2_c2 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 2')
    f2_c3 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 3')
    f2_c4 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 4')
    f2_c5 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 5')
    f2_c6 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 6')
    f2_c7 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 7')
    f2_c8 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 8')
    f2_c9 = models.FloatField(blank=True, null=True, help_text='Score for filter 2, class 9')
    x_tl = models.IntegerField(default=0, help_text="photo bounding box coordinates top left x")
    x_br = models.IntegerField(default=0, help_text="photo bounding box coordinates bottom right x")
    y_tl = models.IntegerField(default=0, help_text="photo bounding box coordinates top left y")
    y_br = models.IntegerField(default=0, help_text="photo bounding box coordinates bottom right y")

