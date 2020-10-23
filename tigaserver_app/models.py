from django.db import models
import uuid
import os
import os.path
import urllib
from PIL import Image
import datetime
from math import floor
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from django.db.models import Max, Min
from tigacrafting.models import CrowdcraftingTask, MoveLabAnnotation, ExpertReportAnnotation, AEGYPTI_CATEGORIES
#from django.core.urlresolvers import reverse
from django.db.models import Count
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User, Group
from tigacrafting.models import SITE_CATEGORIES, TIGER_CATEGORIES_SEPARATED, AEGYPTI_CATEGORIES_SEPARATED, STATUS_CATEGORIES, TIGER_CATEGORIES, Categories
from collections import Counter
from datetime import datetime, timedelta
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
import logging
import tigacrafting.html_utils as html_utils
import pydenticon
import os.path
import tigaserver_project.settings as conf
from django.conf import settings
import pytz
from django.db.models.signals import post_save
from django.dispatch import receiver
from slugify import slugify
from django.utils import translation
from django.template.loader import render_to_string
from tigacrafting.messaging import send_message_android,send_message_ios
from django.utils import translation
from django.utils.translation import ugettext
import json
from django.db.models import Manager as GeoManager
from django.utils.deconstruct import deconstructible
from django.urls import reverse
from django.template.loader import TemplateDoesNotExist
from io import BytesIO
from django.core.files import File
import html.entities
from common.translation import get_locale_for_en, get_translation_in

logger_report_geolocation = logging.getLogger('mosquitoalert.location.report_location')


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

class TigaProfile(models.Model):
    firebase_token = models.TextField('Firebase token associated with the profile', null=True, blank=True,help_text='Firebase token supplied by firebase, suuplied by an registration service (Google, Facebook,etc)', unique=True)
    score = models.IntegerField(help_text='Score associated with profile. This is the score associated with the account', default=0)



class TigaUser(models.Model):
    user_UUID = models.CharField(max_length=36, primary_key=True, help_text='UUID randomly generated on '
                                                                            'phone to identify each unique user. Must be exactly 36 '
                                                                            'characters (32 hex digits plus 4 hyphens).')
    registration_time = models.DateTimeField(auto_now_add=True, help_text='The date and time when user '
                                                                      'registered and consented to sharing '
                                                                 'data. Automatically set by '
                                                                 'server when user uploads registration.')
    device_token = models.TextField('Url to picture that originated the comment', null=True, blank=True,help_text='Device token, used in messaging. Must be supplied by the client')

    score = models.IntegerField(help_text='Score associated with user. This field is used only if the user does not have a profile', default=0)

    score_v2 = models.IntegerField(help_text='Global XP Score. This field is updated whenever the user asks for the score, and is only stored here. The content must equal score_v2_adult + score_v2_bite + score_v2_site', default=0)

    score_v2_adult = models.IntegerField(help_text='Adult reports XP Score.', default=0)

    score_v2_bite = models.IntegerField(help_text='Bite reports XP Score.', default=0)

    score_v2_site = models.IntegerField(help_text='Site reports XP Score.',default=0)

    profile = models.ForeignKey(TigaProfile, related_name='profile_devices', null=True, blank=True, on_delete=models.DO_NOTHING, )

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

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ('user_UUID',)


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
        return self.expiration_time >= datetime.datetime.utcnow().replace(tzinfo=utc)


class MissionTrigger(models.Model):
    mission = models.ForeignKey(Mission, related_name='triggers', on_delete=models.DO_NOTHING, )
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
    mission = models.ForeignKey(Mission, related_name='items', help_text='Mission to which this item is associated.', on_delete=models.DO_NOTHING, )
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
    objects = GeoManager()
    class Meta:
        managed = True
        db_table = 'europe_countries'

    def __unicode__(self):
        return self.name_engl

class Session(models.Model):
    id = models.AutoField(primary_key=True, help_text='Unique identifier of the session. Automatically generated by server when session created.')
    session_ID = models.IntegerField(db_index=True, help_text='The session ID number. Should be an integer that increments by 1 for each session from a given user.')
    user = models.ForeignKey(TigaUser, help_text='user_UUID for the user sending this report. Must be exactly 36 characters (32 hex digits plus 4 hyphens) and user must have already registered this ID.', related_name="user_sessions", on_delete=models.DO_NOTHING)
    session_start_time = models.DateTimeField(help_text='Date and time on phone when the session was started. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".')
    session_end_time = models.DateTimeField(null=True, blank=True, help_text='Date and time on phone when the session was ended. Format as ECMA 262 date time string (e.g. "2014-05-17T12:34:56.123+01:00".')

    class Meta:
        unique_together = ('session_ID', 'user',)


class Report(models.Model):
    version_UUID = models.CharField(max_length=36, primary_key=True, help_text='UUID randomly generated on '
                                                'phone to identify each unique report version. Must be exactly 36 '
                                                'characters (32 hex digits plus 4 hyphens).')
    version_number = models.IntegerField(db_index=True, help_text='The report version number. Should be an integer that increments '
                                                   'by 1 for each repor version. Note that the user keeps only the '
                                                   'most recent version on the device, but all versions are stored on the server.')
    user = models.ForeignKey(TigaUser, help_text='user_UUID for the user sending this report. Must be exactly 36 '
                                                 'characters (32 hex digits plus 4 hyphens) and user must have '
                                                 'already registered this ID.', related_name="user_reports", on_delete=models.DO_NOTHING, )
    report_id = models.CharField(db_index=True, max_length=4, help_text='4-digit alpha-numeric code generated on user phone to '
                                                         'identify each unique report from that user. Digits should '
                                                         'lbe randomly drawn from the set of all lowercase and '
                                                         'uppercase alphabetic characters and 0-9, but excluding 0, '
                                                         'o, and O to avoid confusion if we ever need user to be able to refer to a report ID in correspondence with MoveLab (as was previously the case when we had them sending samples).')
    server_upload_time = models.DateTimeField(auto_now_add=True, help_text='Date and time on server when report '
                                                                           'uploaded. (Automatically generated by '
                                                                           'server.)')
    phone_upload_time = models.DateTimeField(help_text='Date and time on phone when it uploaded fix. Format '
                                                       'as ECMA '
                                                       '262 date time string (e.g. "2014-05-17T12:34:56'
                                                       '.123+01:00".')
    creation_time = models.DateTimeField(help_text='Date and time on phone when first version of report was created. '
                                                   'Format '
                                                       'as ECMA '
                                                       '262 date time string (e.g. "2014-05-17T12:34:56'
                                                       '.123+01:00".')
    version_time = models.DateTimeField(help_text='Date and time on phone when this version of report was created. '
                                                  'Format '
                                                       'as ECMA '
                                                       '262 date time string (e.g. "2014-05-17T12:34:56'
                                                       '.123+01:00".')
    TYPE_CHOICES = (('bite', 'Bite'), ('adult', 'Adult'), ('site', 'Breeding Site'), ('mission', 'Mission'),)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, help_text="Type of report: 'adult', 'site', "
                                                                         "or 'mission'.", )
    mission = models.ForeignKey(Mission, blank=True, null=True, help_text='If this report was a response to a '
                                                                          'mission, the unique id field of that '
                                                                          'mission.', on_delete=models.DO_NOTHING, )
    LOCATION_CHOICE_CHOICES = (('current', "Current location detected by user's device"), ('selected',
                                                                                           'Location selected by '
                                                                                           'user from map'),
                               ('missing', 'No location choice submitted - should be used only for missions'))
    location_choice = models.CharField(max_length=8, choices=LOCATION_CHOICE_CHOICES, help_text='Did user indicate '
                                                                                                'that report relates '
                                                                                                'to current location '
                                                                                                'of phone ("current") or to a location selected manually on the map ("selected")? Or is the choice missing ("missing")')
    current_location_lon = models.FloatField(blank=True, null=True, help_text="Longitude of user's current location. "
                                                                              "In decimal degrees.")
    current_location_lat = models.FloatField(blank=True, null=True, help_text="Latitude of user's current location. "
                                                                              "In decimal degrees.")
    selected_location_lon = models.FloatField(blank=True, null=True, help_text="Latitude of location selected by "
                                                                               "user on map. "
                                                                              "In decimal degrees.")
    selected_location_lat = models.FloatField(blank=True, null=True, help_text="Longitude of location selected by "
                                                                               "user on map. "
                                                                              "In decimal degrees.")
    note = models.TextField(blank=True, null=True, help_text='Note user attached to report.')
    package_name = models.CharField(db_index=True, max_length=400, blank=True, help_text='Name of tigatrapp package from which this '
                                                                          'report was submitted.')
    package_version = models.IntegerField(db_index=True, blank=True, null=True, help_text='Version number of tigatrapp package from '
                                                                           'which this '
                                                                          'report was submitted.')
    device_manufacturer = models.CharField(max_length=200, blank=True, help_text='Manufacturer of device from which '
                                                                                'this '
                                                                          'report was submitted.')
    device_model = models.CharField(max_length=200, blank=True, help_text='Model of device from '
                                                                         'which this '
                                                                          'report was submitted.')
    os = models.CharField(max_length=200, blank=True, help_text='Operating system of device from which this '
                                                                          'report was submitted.')
    os_version = models.CharField(max_length=200, blank=True, help_text='Operating system version of device from '
                                                                        'which this '
                                                                          'report was submitted.')
    os_language = models.CharField(max_length=10, blank=True, help_text='Language setting of operating system on '
                                                                         'device from '
                                                                        'which this '
                                                                          'report was submitted. 2-digit '
                                                                        'ISO-639-1 language code.')
    app_language = models.CharField(max_length=10, blank=True, help_text='Language setting, within tigatrapp, '
                                                                        'of device '
                                                                          'from '
                                                                        'which this '
                                                                          'report was submitted. 2-digit '
                                                                        'ISO-639-1 language code.')

    hide = models.BooleanField(default=False, help_text='Hide this report from public views?')

    # Several viewsets, especially those involving loading hidden/not hidden reports, are EXTREMELY slow. This happens because
    # whether a report is or not visible delegates on show_on_map. This function performs a lot of database queries; so calling
    # this function on all reports takes a lot of time. For unknown reasons, there are a few views which are executed when the
    # app first starts. For example:
    # AllReportsMapViewSetPaginated
    # AllReportsMapViewSet
    # NonVisibleReportsMapViewSet
    # This causes the app to take forever to start and in several occasions leads to timeouts. The solution to avoid this
    # is to create this cached_visible field, and populate with 1 if show_on_map is True, 0 on the contrary. If the value
    # is undefined, show_on_map executes normally. This accelerates a great deal the application startup, but implies that
    # there must be an external periodic task which populates this field
    cached_visible = models.IntegerField(blank=True, null=True, help_text='Precalculated value of show_on_map_function')

    point = models.PointField(blank=True,null=True,srid=4326)

    country = models.ForeignKey(EuropeCountry, blank=True, null=True, on_delete=models.DO_NOTHING, )

    session = models.ForeignKey(Session, blank=True, null=True, help_text='Session ID for session in which this report was created ', related_name="session_reports", on_delete=models.DO_NOTHING)

    objects = GeoManager()

    def __unicode__(self):
        return self.version_UUID

    #this is called previous to saving the object and initializes the spatial field
    #it supplies
    def get_point(self):
        if (self.get_lon() == -1 and self.get_lat() == -1) or self.get_lon() is None or self.get_lat() is None:
            return None
        # longitude, latitude
        wkt_point = 'POINT( {0} {1} )'
        p = GEOSGeometry(wkt_point.format(self.get_lon(), self.get_lat()), srid=4326)
        return p

    def get_country_is_in(self):
        logger_report_geolocation.debug('retrieving country for report with id {0}'.format(self.version_UUID, ))
        if self.point is not None:
            countries = EuropeCountry.objects.filter(geom__contains=self.point)
            logger_report_geolocation.debug('report with id {0} has {1} country candidates'.format(self.version_UUID, len(countries)))
            if len(countries) == 0:
                logger_report_geolocation.debug('report with id {0} has no candidates, assigning to NEARBY country (within 0.1 degrees)'.format(self.version_UUID))
                cursor = connection.cursor()
                # K nearest neighbours,
                # fetch nearest polygon to point, if it's closer than 0.1 degrees (~10km), assign. else, is in the sea
                cursor.execute("""
                    SELECT st_distance(geom, 'SRID=4326;POINT(%s %s)'::geometry) as d, name_engl, gid
                    FROM europe_countries
                    ORDER BY d limit 1
                """, ( self.point.x, self.point.y, ) )
                # Changed this because some odd behaviour which messed the ordering (0 appeared lower than other distances)
                '''
                cursor.execute("""
                    SELECT st_distance(geom, 'SRID=4326;POINT(%s %s)'::geometry) as d,name_engl,gid
                    FROM europe_countries
                    ORDER BY geom <-> 'SRID=4326;POINT(%s %s)'::geometry limit 1
                """, ( self.point.x, self.point.y, self.point.x, self.point.y, ) )
                '''
                row = cursor.fetchone()
                if row[0] < 0.1:
                    c = EuropeCountry.objects.get(pk=row[2])
                    logger_report_geolocation.debug('report with id {0} assigned to NEARBY country {1} with code {2}'.format(self.version_UUID,c.name_engl, c.iso3_code, ))
                    return c
                else:
                    logger_report_geolocation.debug('report with id {0} found no NEARBY countries, setting country as none'.format(self.version_UUID))
                return None
            elif len(countries) == 1:
                logger_report_geolocation.debug('report with id {0} has SINGLE candidate, country {1} with code {2}'.format(self.version_UUID, countries[0].name_engl, countries[0].iso3_code, ))
                return countries[0]
            else: #more than 1 country
                logger_report_geolocation.debug( 'report with id {0} is inside MULTIPLE countries ({1} countries), using country {2} with code {3}'.format( self.version_UUID, countries[0].name_engl, countries[0].name_engl, countries[0].iso3_code, ) )
                return countries[0]

        logger_report_geolocation.debug('report with id {0} has no associated geolocation'.format(self.version_UUID, ))
        return None

    def is_spain(self):
        return self.country is None or self.country.gid == 17

    def get_country_label(self):
        if self.is_spain():
            return "Spain/Other"
        else:
            return "Europe/" + self.country.name_engl

    def get_lat(self):
        if self.location_choice == 'selected' and self.selected_location_lat is not None:
            return self.selected_location_lat
        else:
            return self.current_location_lat

    def get_lon(self):
        if self.location_choice == 'selected' and self.selected_location_lon is not None:
            return self.selected_location_lon
        else:
            return self.current_location_lon

    def has_location(self):
        return self.get_lat() is not None and self.get_lon() is not None

    def get_tigaprob(self):
        these_responses = self.responses.only('answer').values('answer').iterator()
        response_score = 0
        total = 0
        for response in these_responses:
            total += 1
            if 'Y' in response['answer'] or 'S' in response['answer']:
                response_score += 1
            elif 'No' in response.values():
                response_score -= 1
        if total == 0:
            total = 1
        return float(response_score)/total

    def get_tigaprob_cat(self):
        return int(round(2.499999 * self.get_tigaprob(), 0))

    def get_response_html(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID).order_by('question')
        result = ''
        for this_response in these_responses:
            result = result + '<br/>' + this_response.question + '&nbsp;' + this_response.answer
        return result

    def get_response_string(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID).order_by('question')
        result = ''
        for this_response in these_responses:
            result = result + '{' + this_response.question + ' ' + this_response.answer + '}'
        return result

    def get_tigaprob_text(self):
        if self.tigaprob == 1.0:
            return _('High')
        elif 0.0 < self.tigaprob < 1.0:
            return _('Medium')
        else:
            return _('Low')

    def get_site_type(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = ''
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer
        return result

    def get_site_type_trans(self):
        if self.embornals:
            return _('storm-drain')
        if self.fonts:
            return _('Fountain')
        if self.basins:
            return _('Basin')
        if self.wells:
            return _('Well')
        if self.other:
            return _('Other')

    def get_site_embornals(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type') or \
                    this_response.question.startswith('Is this a storm drain') or \
                    this_response.question.startswith(u'\xc9s un embornal') or \
                    this_response.question.startswith(u'\xbfEs un imbornal'):
                result = this_response.answer.startswith('Embornal') or this_response.answer.startswith('Sumidero') or this_response.answer.startswith('Storm') or this_response.answer.startswith('Yes') or this_response.answer.startswith(u'S\xed')
        for this_response in these_responses:
            if this_response.question_id == 12 and this_response.answer_id == 121:
                return True
        return result

    def get_site_fonts(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer.startswith('Font') or this_response.answer.startswith('Fountain') or this_response.answer.startswith('Fuente')
        return result

    def get_site_basins(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer.startswith('Basin') or this_response.answer.startswith('Basses') or this_response.answer.startswith('Balsa') or this_response.answer.startswith('Bassa') or this_response.answer.startswith('Small basin') or 'balsas' in this_response.answer
        return result

    def get_site_buckets(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer.startswith('Bucket') or this_response.answer.startswith('Small container') or this_response.answer.startswith('Bidones') or this_response.answer.startswith('Recipiente') or this_response.answer.startswith('Recipient') or this_response.answer.startswith('Bidons')
        return result

    def get_site_wells(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer == 'Well' or this_response.answer == 'Pozos' or \
                    this_response.answer == 'Pous'
        return result

    def get_site_other(self):
        these_responses = ReportResponse.objects.filter(report__version_UUID=self.version_UUID)
        result = False
        for this_response in these_responses:
            if this_response.question.startswith('Tipo') or this_response.question.startswith('Selecciona') or \
                    this_response.question.startswith('Type'):
                result = this_response.answer == 'Other' or this_response.answer == 'Altres' or \
                    this_response.answer == 'Otros'
        return result

    def get_site_cat(self):
        if self.get_site_embornals():
            return 0
        elif self.get_site_fonts():
            return 1
        elif self.get_site_basins():
            return 2
        elif self.get_site_buckets():
            return 3
        elif self.get_site_wells():
            return 4
        else:
            return 5

    def get_masked_lat(self):
        if self.lat is not None:
            return round(floor(self.lat/.05)*.05, 2)
        else:
            return None

    def get_masked_lon(self):
        if self.lon is not None:
            return round(floor(self.lon/.05)*.05, 2)
        else:
            return None

    def get_n_visible_photos(self):
        return Photo.objects.filter(report__version_UUID=self.version_UUID).exclude(hide=True).count()

    def get_n_photos(self):
        these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID)
        return len(these_photos)

    def get_photo_html(self):
        these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).exclude(hide=True)
        result = ''
        for photo in these_photos:
            result = result + photo.small_image_() + '&nbsp;'
        return result

    def get_photo_html_for_report_validation(self):
        these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).exclude(hide=True)
        result = ''
        for photo in these_photos:
            result += '<div id="div_for_photo_to_display_report_' + str(self.version_UUID) + '"><input type="radio" name="photo_to_display_report_' + str(self.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:</div><br><div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div><br>'
        return result

    def get_photo_html_for_report_validation_superexpert(self):
        these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).exclude(hide=True)
        result = ''

        for photo in these_photos:
            result += '<div id="div_for_photo_to_display_report_' + str(self.version_UUID) + '">' \
                                                                                             '<input type="radio" name="photo_to_display_report_' + str(
                self.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(
                photo.id) + '"/>Display this photo on public map:</div>' \
                            '<br>' \
                            '<div style="border: 1px solid #333333;margin:1px;position: relative;">' + photo.medium_image_for_validation_() + '' \
                                                                                                                                              '<a class="btn btn-default infoPhoto bottom-right" value="' + str(
                self.version_UUID) + '__' + str(photo.id) + '">' \
                                                            '<i aria-hidden="true" title="Image EXIF metadata" class="glyphicon glyphicon-info-sign"></i>' \
                                                            '</a>' \
                                                            '</div><br>'

        return result

    def get_photo_html_for_report_validation_completed(self):
        these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).exclude(hide=True)
        result = ''
        for photo in these_photos:
            result += '<div id="' + str(photo.id) + '" style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div><br>'
        return result

    def get_formatted_date(self):
        return self.version_time.strftime("%d-%m-%Y %H:%M")

    def get_is_deleted(self):
        result = False
        all_versions = Report.objects.filter(report_id=self.report_id).order_by('version_number')
        if all_versions[0].version_number == -1:
            result = True
        return result

    def get_other_versions(self):
        all_versions = Report.objects.filter(report_id=self.report_id).exclude(version_UUID=self.version_UUID).order_by('version_number')
        result = ''
        for this_version in all_versions:
            result += '<a href="/admin/tigaserver_app/report/%s">Version %s</a> ' % (this_version.version_UUID, this_version.version_number)
        return result

    def get_is_latest(self):
        if self.version_number == -1:
            return False
        elif Report.objects.filter(report_id=self.report_id).filter(type=self.type).count() == 1:
            return True
        else:
            all_versions = Report.objects.filter(report_id=self.report_id).filter(type=self.type).order_by('version_number')
            if all_versions[0].version_number == -1:
                return False
            elif all_versions.reverse()[0].version_number == self.version_number:
                return True
            else:
                return False

    def get_which_is_latest(self):
        all_versions = Report.objects.filter(report_id=self.report_id).order_by('version_number')
        return all_versions.reverse()[0].version_UUID

    def get_crowdcrafting_score(self):
        if self.type not in ('site', 'adult'):
            return None
        these_photos = self.photos.exclude(hide=True).annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
        if these_photos.count() == 0:
            return None
        if self.type == 'site':
            scores = map(lambda x: x.crowdcraftingtask.site_validation_score, these_photos.iterator())
        else:
            scores = map(lambda x: x.crowdcraftingtask.tiger_validation_score, these_photos.iterator())
        if scores is None or len(scores) == 0:
            return None
        else:
            return max(scores)

    def get_report_language(self):
        app_language = self.app_language
        if app_language is not None and app_language != '':
            trans_info = translation.get_language_info(app_language)
            return trans_info['name']
        return 'English'

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
        if self.type not in ('site', 'adult'):
            return result
        these_photos = self.photos.exclude(hide=True).annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
        for photo in these_photos:
            result += '<br>' + photo.small_image_() + '<br>'
        return result

    def show_on_map(self):
        if self.creation_time.year == 2014:
            return True
        else:
            if self.cached_visible is None:
                return (not self.photos.all().exists()) or ((ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists()) and self.get_final_expert_status() == 1)
            else:
                return self.cached_visible == 1

    def get_movelab_annotation_euro(self):
        expert_validated = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True)
        if self.creation_time.year == 2014 and not expert_validated:
            if self.type == 'adult':
                max_movelab_annotation = MoveLabAnnotation.objects.filter(task__photo__report=self).exclude(hide=True).order_by('tiger_certainty_category').last()
                if max_movelab_annotation is not None:
                    return {'tiger_certainty_category': max_movelab_annotation.tiger_certainty_category,
                            'crowdcrafting_score_cat': max_movelab_annotation.task.tiger_validation_score_cat,
                            'crowdcrafting_n_response': max_movelab_annotation.task.crowdcrafting_n_responses,
                            'edited_user_notes': max_movelab_annotation.edited_user_notes,
                            'photo_html': max_movelab_annotation.task.photo.popup_image()}
        else:
            if expert_validated:
                result = {'edited_user_notes': self.get_final_public_note()}
                if self.get_final_photo_html():
                    result['photo_html'] = self.get_final_photo_html().popup_image()
                if self.type == 'adult':
                    classification = self.get_final_combined_expert_category_euro_struct()
                    if classification['conflict'] is True:
                        result['class_name'] = 'Conflict'
                        result['class_label'] = 'conflict'
                    else:
                        if classification['category'] is not None:
                            result['class_name'] = classification['category'].name
                            result['class_label'] = slugify(classification['category'].name)
                            result['class_id'] = classification['category'].id
                            result['class_value'] = classification['value']
                        elif classification['complex'] is not None:
                            result['class_name'] = classification['complex'].description
                            result['class_label'] = slugify(classification['category'].description)
                            result['class_id'] = classification['category'].id
                            result['class_value'] = classification['value']
                    '''
                    retval = {
                        'category': None,
                        'complex': None,
                        'value': None,
                        'conflict': False
                    }
                    '''
                elif self.type == 'site':
                    result['class_name'] = "site"
                    result['class_label'] = "site"
                    result['site_certainty_category'] = self.get_final_expert_score()
                return result
        return None

    # note that I am making this really get movelab or expert annotation,
    # but keeping name for now to avoid refactoring templates
    def get_movelab_annotation(self):
        expert_validated = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True)
        if self.creation_time.year == 2014 and not expert_validated:
            if self.type == 'adult':
                max_movelab_annotation = MoveLabAnnotation.objects.filter(task__photo__report=self).exclude(hide=True).order_by('tiger_certainty_category').last()
                if max_movelab_annotation is not None:
                    return {'tiger_certainty_category': max_movelab_annotation.tiger_certainty_category, 'crowdcrafting_score_cat': max_movelab_annotation.task.tiger_validation_score_cat, 'crowdcrafting_n_response': max_movelab_annotation.task.crowdcrafting_n_responses, 'edited_user_notes': max_movelab_annotation.edited_user_notes, 'photo_html': max_movelab_annotation.task.photo.popup_image()}
        else:
            if expert_validated:
                result = {'edited_user_notes': self.get_final_public_note()}
                if self.get_final_photo_html():
                    result['photo_html'] = self.get_final_photo_html().popup_image()
                    if hasattr(self.get_final_photo_html(), 'crowdcraftingtask'):
                        result['crowdcrafting_score_cat'] = self.get_final_photo_html().crowdcraftingtask.tiger_validation_score_cat
                        result['crowdcrafting_n_response'] = self.get_final_photo_html().crowdcraftingtask.crowdcrafting_n_responses
                if self.type == 'adult':
                    result['tiger_certainty_category'] = self.get_final_expert_score()
                    result['aegypti_certainty_category'] = self.get_final_expert_score_aegypti()
                    classification = self.get_mean_combined_expert_adult_score()
                    result['score'] = int(round(classification['score']))
                    if result['score'] <= 0:
                        result['classification'] = 'none'
                    else:
                        if classification['is_aegypti'] == True:
                            result['classification'] = 'aegypti'
                        elif classification['is_albopictus'] == True:
                            result['classification'] = 'albopictus'
                        elif classification['is_none'] == True:
                            result['classification'] = 'none'
                        else:
                            #This should NEVER happen. however...
                            result['classification'] = 'conflict'
                elif self.type == 'site':
                    result['site_certainty_category'] = self.get_final_expert_score()
                return result
        return None

    # Convenience method, used only in the nearby_reports API call
    def get_simplified_adult_movelab_annotation(self):
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True):
            result = {}
            if self.type == 'adult':
                classification = self.get_mean_combined_expert_adult_score()
                result['score'] = int(round(classification['score']))
                if classification['is_aegypti'] == True:
                    result['classification'] = 'aegypti'
                elif classification['is_albopictus'] == True:
                    result['classification'] = 'albopictus'
                elif classification['is_none'] == True:
                    result['classification'] = 'none'
                else:
                    # This should NEVER happen. however...
                    result['classification'] = 'conflict'
            return result
        return None

    # return the aegypti category; if there are several superexperts (shouldn't happen, I think) with certainty values return smallest
    def get_final_superexpert_aegypti_score(self):
        annot = ExpertReportAnnotation.objects.filter(report=self,user__groups__name='superexpert',validation_complete=True).exclude(aegypti_certainty_category__isnull=True).order_by('aegypti_certainty_category').first()
        if annot is not None:
            return annot.aegypti_certainty_category
        return None


    def get_movelab_score(self):
        if self.type != 'adult':
            return None
        max_movelab_annotation = MoveLabAnnotation.objects.filter(task__photo__report=self).exclude(hide=True).order_by('tiger_certainty_category').last()
        if max_movelab_annotation is None:
            return None
        return max_movelab_annotation.tiger_certainty_category

    def get_crowd_score(self):
        if self.type != 'adult':
            return None
        max_movelab_annotation = MoveLabAnnotation.objects.filter(task__photo__report=self).exclude(hide=True).order_by('tiger_certainty_category').last()
        if max_movelab_annotation is None:
            return None
        return max_movelab_annotation.task.tiger_validation_score_cat

    def get_tiger_responses_text(self):
        if self.type != 'adult':
            return None
        these_responses = self.responses.all()
        result = {}
        for response in these_responses:
            result[response.question] = response.answer
        return result

    def get_tiger_responses_json_friendly(self):
        if self.type != 'adult':
            return None
        these_responses = self.responses.all()
        result = {}
        i = 1
        for response in these_responses:
            item = {}
            item["q"] = response.question
            item["a"] = response.answer
            result["q_" + str(i)] = item
            i = i + 1
        return result

    def get_tiger_responses(self):
        if self.type != 'adult':
            return None
        these_responses = self.responses.all()
        result = {}
        if these_responses.filter(Q(question=u'Is it small and black with white stripes?') | Q(question=u'\xc9s petit i negre amb ratlles blanques?') | Q(question=u'\xbfEs peque\xf1o y negro con rayas blancas?')).count() > 0:
            q1r = these_responses.get(Q(question=u'Is it small and black with white stripes?') | Q(question=u'\xc9s petit i negre amb ratlles blanques?') | Q(question=u'\xbfEs peque\xf1o y negro con rayas blancas?')).answer
            result['q1_response'] = 1 if q1r in [u'S\xed', u'Yes'] else -1 if q1r == u'No' else 0
        if these_responses.filter(Q(question=u'Does it have a white stripe on the head and thorax?') | Q(question=u'T\xe9 una ratlla blanca al cap i al t\xf2rax?') | Q(question=u'\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?')).count() > 0:
            q2r = these_responses.get(Q(question=u'Does it have a white stripe on the head and thorax?') | Q(question=u'T\xe9 una ratlla blanca al cap i al t\xf2rax?') | Q(question=u'\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?')).answer
            result['q2_response'] = 1 if q2r in [u'S\xed', u'Yes'] else -1 if q2r == u'No' else 0
        if these_responses.filter(Q(question=u'Does it have white stripes on the abdomen and legs?') | Q(question=u"T\xe9 ratlles blanques a l'abdomen i a les potes?") | Q(question=u'\xbfTiene rayas blancas en el abdomen y en las patas?')).count() > 0:
            q3r = these_responses.get(Q(question=u'Does it have white stripes on the abdomen and legs?') | Q(question=u"T\xe9 ratlles blanques a l'abdomen i a les potes?") | Q(question=u'\xbfTiene rayas blancas en el abdomen y en las patas?')).answer
            result['q3_response'] = 1 if q3r in [u'S\xed', u'Yes'] else -1 if q3r == u'No' else 0
        return result

    # def get_tiger_responses(self):
    #     if self.type != 'adult':
    #         return None
    #     these_responses = self.responses.all()
    #     result = {}
    #
    #     if these_responses.filter(Q(question=u'Is it small and black with white stripes?')|Q(question=u'\xc9s petit i negre amb ratlles blanques?')|Q(question=u'\xbfEs peque\xf1o y negro con rayas blancas?')).count() > 0:
    #         q1r = these_responses.get(Q(question=u'Is it small and black with white stripes?')|Q(question=u'\xc9s petit i negre amb ratlles blanques?')|Q(question=u'\xbfEs peque\xf1o y negro con rayas blancas?')).answer
    #         result['q1_response'] = 1 if q1r in [u'S\xed', u'Yes'] else -1 if q1r == u'No' else 0
    #     elif these_responses.filter(Q(question=u'What does your mosquito look like? Check the (i) button and select an answer:') | Q(question=u'Com \xe9s el teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:') | Q(question=u'\xbfC\xf3mo es tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).count() > 0:
    #         q1r = these_responses.get(Q(question=u'What does your mosquito look like? Check the (i) button and select an answer:') | Q(question=u'Com \xe9s el teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:') | Q(question=u'\xbfC\xf3mo es tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).answer
    #         result['q1_response'] = -2 if q1r in [u'Like Ae. albopictus', u'Com Ae. albopictus',u'Como Ae. albopictus'] else -3 if q1r in [u'Like Ae. aegypti', u'Com Ae. aegypti', u'Como Ae. aegypti'] else -4 if q1r in [u'Neither', u'Cap dels dos', u'None of them'] else -5
    #
    #     if these_responses.filter(Q(question=u'Does it have a white stripe on the head and thorax?')|Q(question=u'T\xe9 una ratlla blanca al cap i al t\xf2rax?')|Q(question=u'\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?')).count() > 0:
    #         q2r = these_responses.get(Q(question=u'Does it have a white stripe on the head and thorax?')|Q(question=u'T\xe9 una ratlla blanca al cap i al t\xf2rax?')|Q(question=u'\xbfTiene una raya blanca en la cabeza y en el t\xf3rax?')).answer
    #         result['q2_response'] = 1 if q2r in [u'S\xed', u'Yes'] else -1 if q2r == u'No' else 0
    #     elif these_responses.filter(Q(question=u'What does the thorax of your mosquito look like? Check the (i) button and select an answer:')|Q(question=u'Com \xe9s el t\xf2rax del teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:')|Q(question=u'\xbfC\xf3mo es el t\xf3rax de tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).count() > 0:
    #         q2r = these_responses.get(Q(question=u'What does the thorax of your mosquito look like? Check the (i) button and select an answer:')|Q(question=u'Com \xe9s el t\xf2rax del teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:')|Q(question=u'\xbfC\xf3mo es el t\xf3rax de tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).answer
    #         result['q2_response'] = -2 if q2r in [u'Thorax like Ae. albopictus', u'T\xf3rax com Ae. albopictus', u'T\xf3rax like Ae. albopictus'] else -3 if q2r in [u'Thorax like Ae. aegypti', u'T\xf3rax com Ae. aegypti', u'T\xf3rax como Ae. aegypti'] else -4 if q2r in [u'Neither', u'Cap dels dos', u'Ninguno de los dos'] else -5
    #
    #     if these_responses.filter(Q(question=u'Does it have white stripes on the abdomen and legs?')|Q(question=u"T\xe9 ratlles blanques a l'abdomen i a les potes?")|Q(question=u'\xbfTiene rayas blancas en el abdomen y en las patas?')).count() > 0:
    #         q3r = these_responses.get(Q(question=u'Does it have white stripes on the abdomen and legs?')|Q(question=u"T\xe9 ratlles blanques a l'abdomen i a les potes?")|Q(question=u'\xbfTiene rayas blancas en el abdomen y en las patas?')).answer
    #         result['q3_response'] = 1 if q3r in [u'S\xed', u'Yes'] else -1 if q3r == u'No' else 0
    #     elif these_responses.filter(Q(question=u'What does the abdomen of your mosquito look like? Check the (i) button and select an answer:')|Q(question=u'Com \xe9s l\u2019abdomen del teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:')|Q(question=u'\xbfC\xf3mo es el abdomen de tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).count() > 0:
    #         q3r = these_responses.get(Q(question=u'What does the abdomen of your mosquito look like? Check the (i) button and select an answer:')|Q(question=u'Com \xe9s l\u2019abdomen del teu mosquit? Consulta el bot\xf3 (i) i selecciona una resposta:')|Q(question=u'\xbfC\xf3mo es el abdomen de tu mosquito? Consulta el bot\xf3n (i) y selecciona una respuesta:')).answer
    #         result['q3_response'] = -2 if q3r in [u'Abdomen like a Ae. albopictus',u'Abdomen com Ae. albopictus',u'Abdomen como Ae. albopictus'] else -3 if q3r in [u'Abdomen like Ae. aegypti', u'Abdomen com Ae. aegypti',u'Abdomen como Ae. aegypti'] else -4 if q3r in [u'Neither', u'Cap dels dos',u'Ninguno de los dos'] else -5
    #     return result

    def get_site_responses_text(self):
        if self.type != 'site':
            return None
        these_responses = self.responses.all()
        result = {}
        for response in these_responses:
            result[response.question] = response.answer
        return result

    def get_site_responses(self):
        if self.type != 'site':
            return None
        these_responses = self.responses.all()
        result = {}
        if self.package_name == 'ceab.movelab.tigatrapp' and self.package_version >= 10:
            if these_responses.filter(Q(question=u'Is it in a public area?')|Q(question=u'\xbfSe encuentra en la v\xeda p\xfablica?')|Q(question=u'Es troba a la via p\xfablica?')).count() > 0:
                q1r = these_responses.get(Q(question=u'Is it in a public area?')|Q(question=u'\xbfSe encuentra en la v\xeda p\xfablica?')|Q(question=u'Es troba a la via p\xfablica?')).answer
                result['q1_response_new'] = 1 if q1r in [u'S\xed', u'Yes'] else -1

            if these_responses.filter(Q(question=u'Does it contain stagnant water and/or mosquito larvae or pupae (any mosquito species)?')|Q(question=u'Contiene agua estancada y/o larvas o pupas de mosquito (cualquier especie)?')|Q(question=u'Cont\xe9 aigua estancada y/o larves o pupes de mosquit (qualsevol esp\xe8cie)?')).count() > 0:
                q2r = these_responses.get(Q(question=u'Does it contain stagnant water and/or mosquito larvae or pupae (any mosquito species)?')|Q(question=u'Contiene agua estancada y/o larvas o pupas de mosquito (cualquier especie)?')|Q(question=u'Cont\xe9 aigua estancada y/o larves o pupes de mosquit (qualsevol esp\xe8cie)?')).answer
                result['q2_response_new'] = 1 if (u'S\xed' in q2r or u'Yes' in q2r) else -1

            if these_responses.filter(Q(question=u'Have you seen adult mosquitoes nearby (<10 meters)?')|Q(question=u'\xbfHas visto mosquitos cerca (a <10 metros)?')|Q(question=u'Has vist mosquits a prop (a <10metres)?')).count() > 0:
                q3r = these_responses.get(Q(question=u'Have you seen adult mosquitoes nearby (<10 meters)?')|Q(question=u'\xbfHas visto mosquitos cerca (a <10 metros)?')|Q(question=u'Has vist mosquits a prop (a <10metres)?')).answer
                result['q3_response_new'] = 1 if q3r in [u'S\xed', u'Yes'] else -1
            return result
        else:
            if these_responses.filter(Q(question=u'Does it have stagnant water inside?')|Q(question=u'\xbfContiene agua estancada?')|Q(question=u'Cont\xe9 aigua estancada?')).count() > 0:
                q1r = these_responses.get(Q(question=u'Does it have stagnant water inside?')|Q(question=u'\xbfContiene agua estancada?')|Q(question=u'Cont\xe9 aigua estancada?')).answer
                result['q1_response'] = 1 if q1r in [u'S\xed', u'Yes'] else -1 if q1r == u'No' else 0
            if these_responses.filter(Q(question=u'Have you seen mosquito larvae (not necessarily tiger mosquito) inside?')|Q(question=u'\xbfContiene larvas o pupas de mosquito (de cualquier especie)?')|Q(question=u'Cont\xe9 larves o pupes de mosquit (de qualsevol esp\xe8cie)?')).count() > 0:
                q2r = these_responses.get(Q(question=u'Have you seen mosquito larvae (not necessarily tiger mosquito) inside?')|Q(question=u'\xbfContiene larvas o pupas de mosquito (de cualquier especie)?')|Q(question=u'Cont\xe9 larves o pupes de mosquit (de qualsevol esp\xe8cie)?')).answer
                result['q2_response'] = 1 if q2r in [u'S\xed', u'Yes'] else -1 if q2r == u'No' else 0
            return result

    def get_creation_year(self):
        return self.creation_time.year

    def get_creation_month(self):
        return self.creation_time.month

    def get_creation_date(self):
        return self.creation_time.date()

    def get_creation_day_since_launch(self):
        return (self.creation_time - settings.START_TIME).days

    def get_n_expert_report_annotations_tiger_certainty(self):
        n = ExpertReportAnnotation.objects.filter(report=self).exclude(tiger_certainty_category=None).count()
        return n

    def get_n_expert_report_annotations_site_certainty(self):
        n = ExpertReportAnnotation.objects.filter(report=self).exclude(site_certainty_category=None).count()
        return n

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

    def get_final_combined_expert_category_public_map(self,locale):
        classification = self.get_mean_combined_expert_adult_score()
        score = int(round(classification['score']))

        ca = {'tiger':'Mosquit tigre','yellow':'Mosquit febre groga','unclassified':'No identificable','other': 'Altres especies'}
        es = {'tiger':'Mosquito tigre','yellow':'Mosquito fiebre amarilla','unclassified':'No identificable','other': 'Otras especies'}
        en = {'tiger':'Tiger mosquito','yellow':'Yellow fever mosquito','unclassified':'Unidentifiable', 'other': 'Other species'}
        labels = {'ca':ca, 'es':es, 'en':en}

        if classification['is_aegypti']:
            if score == 1 or score == 2:
                return labels[locale]['yellow']
        elif classification['is_albopictus']:
            if score == 1 or score == 2:
                return labels[locale]['tiger']
        else:
            if score == 0 or score == -3:
                return labels[locale]['unclassified']
            elif score == -1 or score == -2:
                return labels[locale]['other']

    def get_translated_species_name(self,locale,untranslated_species):
        current_locale = 'en'
        for l in settings.LANGUAGES:
            if locale==l[0]:
                current_locale = locale
        translation.activate(current_locale)
        translations_table_species_name = {
            "Unclassified": ugettext("species_unclassified"),
            "Other species": ugettext("species_other"),
            "Aedes albopictus": ugettext("species_albopictus"),
            "Aedes aegypti": ugettext("species_aegypti"),
            "Aedes japonicus": ugettext("species_japonicus"),
            "Aedes koreicus": ugettext("species_koreicus"),
            "Complex": ugettext("species_complex"),
            "Not sure": ugettext("species_notsure"),
            "Culex sp.": ugettext("species_culex")
        }
        retval = translations_table_species_name.get(untranslated_species, "Unknown")
        translation.deactivate()
        return retval

    def get_translated_value_name(self, locale, untranslated_value):
        current_locale = 'en'
        for l in settings.LANGUAGES:
            if locale == l[0]:
                current_locale = locale
        translation.activate(current_locale)
        translations_table_value_name = {
            1: ugettext("species_value_possible"),
            2: ugettext("species_value_confirmed")
        }
        retval = translations_table_value_name.get(untranslated_value, "Unknown")
        translation.deactivate()
        return retval

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
                    return self.get_translated_species_name(locale,untranslated_category) + " - " + self.get_translated_value_name(locale,untranslated_certainty)
                else:
                    return self.get_translated_species_name(locale,untranslated_category)



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

    '''
    def get_most_voted_category(self,expert_annotations):
        score_table = {}
        most_frequent_item, most_frequent_count = None, 0
        for anno in expert_annotations:                            
            item = anno.category if anno.complex is None else anno.complex
            score_table[item] = score_table.get(item,0) + 1
            if score_table[item] >= most_frequent_count:
                most_frequent_count, most_frequent_item = score_table[item], item
        # if there's a single key and it's Not sure, then not sure
        if len(score_table.keys()) == 1:
            for key in score_table:
                if key.id == 9:
                    return score_table[key]
        # check for ties
        for key in score_table:            
            score = score_table[key]
            if key != most_frequent_item and score >= most_frequent_count:
                return None #conflict
        return most_frequent_item
    '''

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

    def get_selector_data(self):
        retVal = {
            'id_category' : '',
            'id_complex' : '',
            'validation_value': ''
        }
        superexpert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert',validation_complete=True, revise=True,category__isnull=False)
        expert_annotations = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True, category__isnull=False)

        most_voted = None
        if superexpert_annotations.count() > 1:
            most_voted = self.get_most_voted_category(superexpert_annotations)
        elif superexpert_annotations.count() == 1:
            most_voted = superexpert_annotations[0].category
        elif expert_annotations.count() >= 3:
            most_voted = self.get_most_voted_category(expert_annotations)
        else:
            retVal['id_category'] = None

        if most_voted is None:
            retVal['id_category'] = -1
        else:
            retVal['id_category'] = most_voted.id
            if most_voted.__class__.__name__ == 'Categories':
                if most_voted.specify_certainty_level == True:
                    score = self.get_score_for_category_or_complex(most_voted)
                    retVal['validation_value'] = score
            elif most_voted.__class__.__name__ == 'Complex':
                retVal['id_complex'] = most_voted.id
        return retVal

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

    def get_final_combined_expert_category(self):
        # if self.type == 'site':
        #      return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_final_expert_score()]
        # elif self.type == 'adult':
        #      return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES_SEPARATED))[self.get_final_expert_score()]
        classification = self.get_mean_combined_expert_adult_score()
        score = int(round(classification['score']))
        if score == -4:
            return "Conflict"
        if score <= 0:
            return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES))[score]
        else:
            if classification['is_aegypti']:
                return dict([(-3, 'Unclassified')] + list(AEGYPTI_CATEGORIES_SEPARATED))[score]
            elif classification['is_albopictus'] or classification['is_none']:
                return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES_SEPARATED))[score]
            else:
                return "Conflict"

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

    def get_final_combined_expert_score_euro(self):
        score = -3
        if self.type == 'site':
            score = self.get_mean_expert_site_score()
        elif self.type == 'adult':
            classification = self.get_mean_combined_expert_adult_score_euro()
            score = classification['score']
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_combined_expert_score(self):
        score = -3
        if self.type == 'site':
            score = self.get_mean_expert_site_score()
        elif self.type == 'adult':
            classification = self.get_mean_combined_expert_adult_score()
            score = classification['score']
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_score(self):
        score = -3
        if self.type == 'site':
            score = self.get_mean_expert_site_score()
        elif self.type == 'adult':
            score = self.get_mean_expert_adult_score()
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_score_aegypti(self):
        score = -3
        if self.type == 'site':
            score = self.get_mean_expert_site_score()
        elif self.type == 'adult':
            score = self.get_mean_expert_adult_score_aegypti()
        if score is not None:
            return int(round(score))
        else:
            return -3

    def get_final_expert_category(self):
        if self.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_final_expert_score()]
        elif self.type == 'adult':
            return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES_SEPARATED))[self.get_final_expert_score()]

    def get_final_expert_category_aegypti(self):
        if self.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_final_expert_score()]
        elif self.type == 'adult':
            return dict([(-3, 'Unclassified')] + list(AEGYPTI_CATEGORIES_SEPARATED))[self.get_final_expert_score_aegypti()]

    def get_final_expert_status(self):
        result = 1
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, status=-1).exists():
            result = -1
        elif ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, status=0).exists():
            result = 0
        elif ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, status=1).exists():
            result = 1
        elif ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, status=-1).exists():
            result = -1
        elif ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, status=0).exists():
            result = 0
        elif ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, status=1).exists():
            result = 1
        return result

    def get_final_expert_status_text(self):
        return dict(STATUS_CATEGORIES)[self.get_final_expert_status()]

    def get_final_expert_status_bootstrap(self):
        result = '<span data-toggle="tooltip" data-placement="bottom" title="' + self.get_final_expert_status_text() + '" class="' + ('glyphicon glyphicon-eye-open' if self.get_final_expert_status() == 1 else ('glyphicon glyphicon-flag' if self.get_final_expert_status() == 0 else 'glyphicon glyphicon-eye-close')) + '"></span>'
        return result

    def is_validated_by_two_experts_and_superexpert(self):
        """
        This is used to locate reports validated by two experts and the superexpert. This commonly
        happens as a consequence of detecting some reports validated 2 times by the same expert; to solve
        this situation, one of the two repeated annotations is removed. As a consequence, the report
        is validated by 2 experts and 1 superexpert
        :return: True if the report is validqted by exactly 2 experts and 1 superexpert
        """
        return ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert',validation_complete=True).count() == 2 and ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True).count() == 1

    def get_is_expert_validated(self):
        return ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True).count() >= 3

    def get_final_expert_score_bootstrap(self):
        result = '<span class="label label-default" style="background-color:' + ('red' if self.get_final_expert_score() == 2 else ('orange' if self.get_final_expert_score() == 1 else ('white' if self.get_final_expert_score() == 0 else ('grey' if self.get_final_expert_score() == -1 else 'black')))) + ';">' + self.get_final_expert_category() + '</span>'
        return result

    def get_tags(self):
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        s = set()
        for ano in these_annotations:
            tags = ano.tags.all()
            for tag in tags:
                s.add(tag)
        return s

    def get_tags_string(self):
        result = ''
        s = self.get_tags()
        if s:
            i = 0
            for tag in s:
                result += tag.name
                if i != len(s) - 1:
                    result += ','
                i += 1
        return result

    def get_tags_bootstrap(self):
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        result = ''
        s = set()
        for ano in these_annotations:
            tags = ano.tags.all()
            for tag in tags:
                if not tag in s:
                    s.add(tag)
                    result += '<span class="label label-success" data-toggle="tooltip" title="tagged by ' + ano.user.username + '" data-placement="bottom">' + (tag.name) + '</span>'
        if(len(s)==0):
            return '<span class="label label-default" data-toggle="tooltip" data-placement="bottom" title="tagged by no one">No tags</span>'
        return result

    def get_single_report_view_link(self):
        result = reverse('single_report_view', kwargs={"version_uuid": self.version_UUID})
        return result

    def get_who_has_list(self):
        result = []
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        i = these_annotations.count()
        for ano in these_annotations:
            result.append(ano.user.username)
        return result

    def get_who_has_message_recipients(self):
        result = ''
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        i = these_annotations.count()
        for ano in these_annotations:
            result += ano.user.username
            i -= 1
            if i > 0:
                result += '+'
        return result

    def user_has_report(self, user):
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        assigned_to = []
        for ano in these_annotations:
            assigned_to.append(ano.user)
        return user in assigned_to

    def get_who_has(self):
        result = ''
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        i = these_annotations.count()
        for ano in these_annotations:
            result += ano.user.username + (': validated' if ano.validation_complete else ': pending')
            i -= 1
            if i > 0:
                result += ', '
        return result

    def get_who_has_count(self):
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        i = these_annotations.count()
        return i

    def get_annotations(self):
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        return these_annotations

    def get_expert_recipients(self):
        result = []
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        for ano in these_annotations:
            if not ano.user.userstat.is_superexpert():
                result.append(ano.user.username)
        return '+'.join(result)

    def get_superexpert_completed_recipients(self):
        result = []
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        for ano in these_annotations:
            if ano.validation_complete and ano.user.userstat.is_superexpert():
                result.append(ano.user.username)
        return '+'.join(result)

    def get_who_has_bootstrap(self):
        result = ''
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        i = these_annotations.count()
        for ano in these_annotations:
            result += '<span class="label ' + ('label-success' if ano.validation_complete else 'label-warning') + '" data-toggle="tooltip" data-placement="bottom" title="' + (('validated by ' + ano.user.username) if ano.validation_complete else ('pending with ' + ano.user.username)) + '">' + ano.user.username + ' <span class="glyphicon ' + ('glyphicon-check' if ano.validation_complete else 'glyphicon-time') + '"></span></span>'
            i -= 1
            if i > 0:
                result += ' '
        return result

    def get_expert_score_reports_bootstrap(self, user=None):
        result = ''
        these_annotations = ExpertReportAnnotation.objects.filter(report=self)
        if user:
            these_annotations.exclude(user=user)
        for ano in these_annotations:
            result += '<div class="table-responsive"><table class="table table-condensed"><tbody><tr>'
            result += '<td>' + ano.user.username + '</td>'
            result += '<td>' + ano.get_status_bootstrap() + '</td>'
            result += '<td>' + ano.get_score_bootstrap() + '</td>'
            result += '<td><a role="button" data-toggle="collapse" href="#expert_collapse' + ano.report.version_UUID + str(ano.id) + '" aria-expanded="false" aria-controls="expert_collapse' + ano.report.version_UUID + str(ano.id) + '"><i class="fa fa-plus-square-o"></i></a></td>'
            result += '</tr></tbody></table></div>'
            result += '<div class="collapse" id="expert_collapse' + ano.report.version_UUID + str(ano.id) + '"><div class="well">'
            result += '<div class="table-responsive"><table class="table table-condensed"><tbody>'
            result += '<tr><td><strong>Expert:</strong></td><td>' + ano.user.username + '</td></tr>'
            result += '<tr><td><strong>Last Edited:</strong></td><td>' + ano.last_modified.strftime("%d %b %Y %H:%m") + ' UTC</td>></tr>'
            if self.type == 'adult':
                result += '<tr><td><strong>Tiger Notes:</strong></td><td>' + ano.tiger_certainty_notes + '</td></tr>'
            elif self.type == 'site':
                result += '<tr><td><strong>Site Notes:</strong></td><td>' + ano.site_certainty_notes + '</td></tr>'
            result += '<tr><td><strong>Selected photo:</strong></td><td>' + (ano.best_photo.popup_image() if ano.best_photo else "") + '</td></tr>'
            result += '<tr><td><strong>Edited User Notes:</strong></td><td>' + ano.edited_user_notes + '</td></tr>'
            result += '<tr><td><strong>Message To User:</strong></td><td>' + ano.message_for_user + '</td></tr>'
            result += '</tbody></table></div></div></div>'
        return result

    def get_expert_annotations_html(self, this_user):
        result = ''
        for ano in self.expert_report_annotations.exclude(user=this_user):
            result += '<p>User: ' + ano.user.username + ', Last Edited: ' + str(ano.last_modified) + '</p>'
            if self.type == 'adult':
                result += '<p>Tiger Certainty: ' + (ano.get_tiger_certainty_category_display() if ano.get_tiger_certainty_category_display() else "") + '</p>'
                result += '<p>Tiger Notes: ' + ano.tiger_certainty_notes + '</p>'
            elif self.type == 'site':
                result += '<p>Site Certainty: ' + (ano.get_site_certainty_category_display() if ano.get_site_certainty_category_display() else "") + '</p>'
                result += '<p>Site Notes: ' + ano.site_certainty_notes + '</p>'
            result += '<p>Status: ' + str(ano.statu) + '</p>'
        return result

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
        photos = Photo.objects.filter(report=self)
        for photo in photos:
            if not photo.hide:
                return photo
        return None

    def get_final_photo_html(self):
        if ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True).exists():
            super_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='superexpert', validation_complete=True, revise=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if super_photos:
                winning_photo_id = Counter(super_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id)
            return None
        else:
            expert_photos = ExpertReportAnnotation.objects.filter(report=self, user__groups__name='expert', validation_complete=True, best_photo__isnull=False).values_list('best_photo', flat=True)
            if expert_photos:
                winning_photo_id = Counter(expert_photos).most_common()[0][0]
                if winning_photo_id:
                    winning_photo = Photo.objects.filter(pk=winning_photo_id)
                    if winning_photo and winning_photo.count() > 0:
                        return Photo.objects.get(pk=winning_photo_id)
            else:
                photos = Photo.objects.filter(report=self)
                if photos and len(photos) == 1:
                    if photos[0] and not photos[0].hide:
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

    def can_be_first_of_season(self, year):
        utc = pytz.UTC
        # naive datetime
        d = datetime(year, conf.SEASON_START_MONTH, conf.SEASON_START_DAY)
        # localized datetime
        ld = utc.localize(d)
        return self.creation_time >= ld

    # save is overriden to initialize the point spatial field with the coordinates supplied
    # to the Report object. See method get_point
    def save(self, *args, **kwargs):
        if not self.point:
            self.point = self.get_point()
        if not self.country:
            c = self.get_country_is_in()
            if c is None:
                logger_report_geolocation.debug('report with id {0} assigned to no country'.format(self.version_UUID,))
            else:
                logger_report_geolocation.debug('report with id {0} assigned to country {1} with code {2}'.format(self.version_UUID,c.name_engl,c.iso3_code,))
            self.country = c

        super(Report, self).save(*args, **kwargs)

    lon = property(get_lon)
    lat = property(get_lat)
    tigaprob = property(get_tigaprob)
    tigaprob_cat = property(get_tigaprob_cat)
    tigaprob_text = property(get_tigaprob_text)
    site_type = property(get_site_type)
    site_type_trans = property(get_site_type_trans)
    site_cat = property(get_site_cat)
    embornals = property(get_site_embornals)
    fonts = property(get_site_fonts)
    basins = property(get_site_basins)
    buckets = property(get_site_buckets)
    wells = property(get_site_wells)
    other = property(get_site_other)
    masked_lat = property(get_masked_lat)
    masked_lon = property(get_masked_lon)
    n_photos = property(get_n_photos)
    n_visible_photos = property(get_n_visible_photos)
    photo_html = property(get_photo_html)
    photo_html_for_report_validation= property(get_photo_html_for_report_validation)
    photo_html_for_report_validation_superexpert = property(get_photo_html_for_report_validation_superexpert)
    formatted_date = property(get_formatted_date)
    response_html = property(get_response_html)
    response_string = property(get_response_string)
    deleted = property(get_is_deleted)
    other_versions = property(get_other_versions)
    latest_version = property(get_is_latest)
    visible = property(show_on_map)
    movelab_annotation = property(get_movelab_annotation)
    movelab_annotation_euro = property(get_movelab_annotation_euro)
    simplified_annotation = property(get_simplified_adult_movelab_annotation)
    movelab_score = property(get_movelab_score)
    crowd_score = property(get_crowd_score)
    tiger_responses = property(get_tiger_responses)
    tiger_responses_text = property(get_tiger_responses_text)
    site_responses = property(get_site_responses)
    site_responses_text = property(get_site_responses_text)
    creation_date = property(get_creation_date)
    creation_day_since_launch = property(get_creation_day_since_launch)
    creation_year = property(get_creation_year)
    creation_month = property(get_creation_month)
    n_photos = property(get_n_photos)
    final_expert_status_text = property(get_final_expert_status)
    is_validated_by_two_experts_and_superexpert = property(is_validated_by_two_experts_and_superexpert)
    country_label = property(get_country_label)
    language = property(get_report_language)
    located = property(has_location)
    is_spain_p = property(is_spain)

    class Meta:
        unique_together = ("user", "version_UUID")


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
    reports = Report.objects.filter(user__user_UUID__in=user_uuids).exclude(type='bite')
    last_versions = filter(lambda x: not x.deleted and x.latest_version, reports)
    return len(list(last_versions))

# def get_translation_in(string, locale):
#     translation.activate(locale)
#     val = ugettext(string)
#     translation.deactivate()
#     return val
#
# def get_locale_for_en(report):
#     if report is not None:
#         if report.app_language is not None and report.app_language != '':
#             if report.app_language != 'ca' and report.app_language != 'en' and report.app_language != 'es':
#                 report_locale = report.app_language
#                 for lang in settings.LANGUAGES:
#                     if lang[0] == report_locale:
#                         return report_locale
#     return 'en'


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
            context_es = {}
            context_ca = {}
            context_en = {}
            locale_for_en = get_locale_for_en(report)

            super_movelab = User.objects.get(pk=24)
            notification_content.title_es = "¡Acabas de recibir una recompensa de puntos!"
            notification_content.title_ca = "Acabes de rebre una recompensa de punts!"
            notification_content.title_en = get_translation_in("you_just_received_a_points_award",locale_for_en)
            if report is not None:
                if report.get_final_photo_url_for_notification():
                    context_es['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                    context_en['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                    context_ca['picture_link'] = 'http://' + current_domain + report.get_final_photo_url_for_notification()
                else:
                    pic = report.get_first_visible_photo()
                    if pic:
                        pic_url = pic.get_medium_url()
                        if pic_url is not None:
                            context_es['picture_link'] = 'http://' + current_domain + pic_url
                            context_en['picture_link'] = 'http://' + current_domain + pic_url
                            context_ca['picture_link'] = 'http://' + current_domain + pic_url

            context_es['amount_awarded'] = xp_amount
            context_en['amount_awarded'] = xp_amount
            context_ca['amount_awarded'] = xp_amount

            context_es['reason_awarded'] = get_translation_in(reason_label, 'es')
            context_en['reason_awarded'] = get_translation_in(reason_label, locale_for_en)
            context_ca['reason_awarded'] = get_translation_in(reason_label, 'ca')

            notification_content.body_html_es = render_to_string('tigaserver_app/award_notification_es.html', context_es)
            notification_content.body_html_ca = render_to_string('tigaserver_app/award_notification_ca.html', context_ca)
            try:
                notification_content.body_html_en = render_to_string('tigaserver_app/award_notification_' + locale_for_en + '.html', context_en)
            except TemplateDoesNotExist:
                notification_content.body_html_en = render_to_string('tigaserver_app/award_notification_en.html',context_en)


            notification_content.body_html_es = notification_content.body_html_es.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')
            notification_content.body_html_ca = notification_content.body_html_ca.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')
            notification_content.body_html_en = notification_content.body_html_en.encode('ascii', 'xmlcharrefreplace').decode('UTF-8')


            '''
            if conf.DEBUG == True:
                print(notification_content.body_html_es)
                print(notification_content.body_html_ca)
                print(notification_content.body_html_en)
            '''
            notification_content.save()
            notification = Notification(report=report, user=report.user, expert=super_movelab, notification_content=notification_content)
            notification.save()

            recipient = report.user
            if recipient.device_token is not None and recipient.device_token != '':
                if (recipient.user_UUID.islower()):
                    try:
                        #print(recipient.user_UUID)
                        send_message_android(recipient.device_token, notification_content.title_es, '')
                    except Exception as e:
                        pass
                else:
                    try:
                        #print(recipient.user_UUID)
                        send_message_ios(recipient.device_token, notification_content.title_es, '')
                    except Exception as e:
                        pass

@receiver(post_save, sender=Report)
def maybe_give_awards(sender, instance, created, **kwargs):
    #only for adults and sites
    if created:
        try:
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
            if instance.type == 'adult' or instance.type == 'site':
                # check award for first of season
                current_year = instance.creation_time.year
                awards = Award.objects.filter(given_to=instance.user).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season')
                if awards.count() == 0:  # not yet awarded
                    if instance.can_be_first_of_season(current_year):  # can be first of season?
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
                awards = Award.objects\
                    .filter(report__creation_time__year=report_year)\
                    .filter(report__creation_time__month=report_month)\
                    .filter(report__creation_time__day=report_day) \
                    .filter(report__user=instance.user) \
                    .filter(category__category_label='daily_participation').order_by('report__creation_time') #first is oldest
                if awards.count() == 0: # not yet awarded
                    grant_first_of_day(instance, super_movelab)
                    issue_notification(instance, DAILY_PARTICIPATION, get_xp_value_of_category(DAILY_PARTICIPATION), conf.HOST_NAME)

                date_1_day_before_report = instance.creation_time - timedelta(days=1)
                date_1_day_before_report_adjusted = date_1_day_before_report.replace(hour=23, minute=59, second=59)
                report_before_this_one = Report.objects.filter(user=instance.user).filter(creation_time__lte=date_1_day_before_report_adjusted).order_by('-creation_time').first() #first is most recent
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
    report = models.ForeignKey(Report, related_name='responses', help_text='Report to which this response is associated.', on_delete=models.DO_NOTHING, )
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


class Photo(models.Model):
    """
    Photo uploaded by user.
    """
    photo = models.ImageField(upload_to=make_image_uuid, help_text='Photo uploaded by user.')
    report = models.ForeignKey(Report, related_name='photos', help_text='Report and version to which this photo is associated (36-digit '
                                                 'report_UUID).', on_delete=models.DO_NOTHING, )
    hide = models.BooleanField(default=False, help_text='Hide this photo from public views?')
    uuid = models.CharField(max_length=36, default=make_uuid)

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


class Fix(models.Model):
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
    body_html_es = models.TextField(help_text='Expert comment, expanded and allows html, in spanish')
    body_html_ca = models.TextField(default=None,blank=True,null=True,help_text='Expert comment, expanded and allows html, in catalan')
    body_html_en = models.TextField(default=None,blank=True,null=True,help_text='Expert comment, expanded and allows html, in english')
    title_es = models.TextField(help_text='Title of the comment, shown in non-detail view, in spanish')
    title_ca = models.TextField(default=None,blank=True,null=True,help_text='Title of the comment, shown in non-detail view, in catalan')
    title_en = models.TextField(default=None,blank=True,null=True,help_text='Title of the comment, shown in non-detail view, in english')

    def get_title_locale_safe(self, locale):
        if locale.lower().startswith('es'):
            return self.title_es
        elif locale.lower().startswith('ca'):
            if self.title_ca is None:
                return self.title_es
            else:
                return self.title_ca
        elif locale.lower().startswith('en'):
            if self.title_en is None:
                return self.title_es
            else:
                return self.title_en
        else:
            return self.title_en
        # elif locale.lower() == 'zh_cn' or locale.lower().startswith('zh'):
        #     return self.title_en
        # else:
        #     return self.title_es

    def get_body_locale_safe(self,locale):
        if locale.lower().startswith('es'):
            return self.body_html_es
        elif locale.lower().startswith('ca'):
            if self.body_html_ca is None:
                return self.body_html_es
            else:
                return self.body_html_ca
        elif locale.lower().startswith('en'):
            if self.body_html_en is None:
                return self.body_html_es
            else:
                return self.body_html_en
        else:
            return self.body_html_en
        # elif locale.lower() == 'zh_cn' or locale.lower().startswith('zh'):
        #     return self.body_html_en
        # else:
        #     return self.body_html_es

class Notification(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', blank=True, related_name='report_notifications', help_text='Report regarding the current notification', on_delete=models.DO_NOTHING, )
    user = models.ForeignKey(TigaUser, related_name="user_notifications", help_text='User to which the notification will be sent', on_delete=models.DO_NOTHING, )
    expert = models.ForeignKey(User, blank=True, related_name="expert_notifications", help_text='Expert sending the notification', on_delete=models.DO_NOTHING, )
    date_comment = models.DateTimeField(auto_now_add=True)
    #blank is True to avoid problems in the migration, this should be removed!!
    notification_content = models.ForeignKey(NotificationContent,blank=True, null=True,related_name="notification_content",help_text='Multi language content of the notification', on_delete=models.DO_NOTHING, )
    #All this becomes obsolete, now all notification text is outside. This allows for re-use in massive notifications
    expert_comment = models.TextField('Expert comment', help_text='Text message sent to user')
    expert_html = models.TextField('Expert comment, expanded and allows html', help_text='Expanded message information goes here. This field can contain HTML')
    photo_url = models.TextField('Url to picture that originated the comment', null=True, blank=True, help_text='Relative url to the public report photo')
    acknowledged = models.BooleanField(default=False,help_text='This is set to True through the public API, when the user signals that the message has been received')
    public = models.BooleanField(default=False,help_text='Whether the notification is shown in the public map or not')


class AwardCategory(models.Model):
    category_label = models.TextField(help_text='Coded label for the translated version of the award. For instance award_good_picture. This code refers to strings in several languages')
    xp_points = models.IntegerField(help_text='Number of xp points associated to this kind of award')
    category_long_description = models.TextField(default=None, blank=True, null=True, help_text='Long description specifying conditions in which the award should be conceded')


class Award(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', default=None, blank=True, null=True, related_name='report_award', help_text='Report which the award refers to. Can be blank for arbitrary awards', on_delete=models.DO_NOTHING, )
    date_given = models.DateTimeField(default=datetime.now, help_text='Date in which the award was given')
    given_to = models.ForeignKey(TigaUser, blank=True, null=True, related_name="user_awards", help_text='User to which the notification was awarded. Usually this is the user that uploaded the report, but the report can be blank for special awards', on_delete=models.DO_NOTHING, )
    expert = models.ForeignKey(User, blank=True, related_name="expert_awards", help_text='Expert that gave the award', on_delete=models.DO_NOTHING, )
    category = models.ForeignKey(AwardCategory, blank=True, null=True, related_name="category_awards", help_text='Category to which the award belongs. Can be blank for arbitrary awards', on_delete=models.DO_NOTHING, )
    special_award_text = models.TextField(default=None, blank=True, null=True, help_text='Custom text for custom award')
    special_award_xp = models.IntegerField(default=0, blank=True, null=True, help_text='Custom xp awarded')

    def __str__(self):
        if self.category:
            return str(self.category.category_label)
        else:
            return self.special_award_text