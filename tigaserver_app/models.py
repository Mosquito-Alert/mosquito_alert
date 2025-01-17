from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime, timedelta
import json
import re
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Message, Notification as FirebaseNotification, AndroidConfig, AndroidNotification, SendResponse, BatchResponse
import logging
from math import floor
from numpyencoder import NumpyEncoder
from PIL import Image
import pydenticon
import os
from slugify import slugify
from typing import Optional, Union
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance as DistanceMeasure
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Count, Q
from django.db.models.base import ModelBase
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import translation, timezone
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from fcm_django.models import AbstractFCMDevice, DeviceType
from imagekit.processors import ResizeToFit
from langcodes import Language, closest_supported_match, standardize_tag as standarize_language_tag, tag_is_valid as language_tag_is_valid
from simple_history.models import HistoricalRecords
from timezone_field import TimeZoneField
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

from tigacrafting.models import MoveLabAnnotation, ExpertReportAnnotation, Categories, STATUS_CATEGORIES
import tigacrafting.html_utils as html_utils
import tigaserver_project.settings as conf

from .fields import ProcessedImageField
from .managers import ReportManager, PhotoManager, NotificationManager, DeviceManager
from .messaging import send_new_award_notification
from .mixins import TimeZoneModelMixin

logger_report_geolocation = logging.getLogger('mosquitoalert.location.report_location')
logger_notification = logging.getLogger('mosquitoalert.notification')

User = get_user_model()

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


class RankingData(models.Model):
    user_uuid = models.CharField(max_length=36, primary_key=True, help_text='User identifier uuid')
    class_value = models.CharField(max_length=60)
    rank = models.IntegerField()
    score_v2 = models.IntegerField()
    last_update = models.DateTimeField(help_text="Last time ranking data was updated", null=True, blank=True)


class TigaUser(AbstractBaseUser, AnonymousUser):

    AVAILABLE_LANGUAGES = [
        (standarize_language_tag(code), Language.get(code).autonym().title()) for code, _ in settings.LANGUAGES
    ]

    USERNAME_FIELD = 'pk'

    password = models.CharField(_('password'), max_length=128, null=True, blank=True)

    user_UUID = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False, help_text='UUID randomly generated on '
                                                                            'phone to identify each unique user. Must be exactly 36 '
                                                                            'characters (32 hex digits plus 4 hyphens).')
    registration_time = models.DateTimeField(auto_now_add=True, help_text='The date and time when user '
                                                                      'registered and consented to sharing '
                                                                 'data. Automatically set by '
                                                                 'server when user uploads registration.')

    score = models.IntegerField(help_text='Score associated with user. This field is used only if the user does not have a profile', default=0)

    score_v2 = models.IntegerField(help_text='Global XP Score. This field is updated whenever the user asks for the score, and is only stored here. The content must equal score_v2_adult + score_v2_bite + score_v2_site', default=0)

    score_v2_adult = models.IntegerField(help_text='Adult reports XP Score.', default=0)

    score_v2_bite = models.IntegerField(help_text='Bite reports XP Score.', default=0)

    score_v2_site = models.IntegerField(help_text='Site reports XP Score.',default=0)

    # NOTE using NumpyEncoder since compute_user_score_in_xp_v2 function get result from pandas dataframe
    # and some integer are np.int64, which can not be encoded with the regular json library setup.
    score_v2_struct = models.JSONField(encoder=NumpyEncoder, help_text="Full cached score data", null=True, blank=True)

    last_score_update = models.DateTimeField(help_text="Last time score was updated", null=True, blank=True)

    last_location = models.PointField(null=True, blank=True, srid=4326)
    last_location_update = models.DateTimeField(help_text="Last time location was updated", null=True, blank=True)

    locale = models.CharField(
        choices=AVAILABLE_LANGUAGES,
        max_length=16,
        default='en',
        validators=[language_tag_is_valid],
        help_text="The locale code representing the language preference selected by the user for displaying the interface text. Enter the locale following the BCP 47 standard in 'language' or 'language-region' format (e.g., 'en' for English, 'en-US' for English (United States), 'fr' for French). The language is a two-letter ISO 639-1 code, and the region is an optional two-letter ISO 3166-1 alpha-2 code."
    )

    @property
    def language_iso2(self):
        return Language.get(self.locale).language.lower()

    @property
    def last_device(self) -> Optional['Device']:
        try:
            return self.devices.latest('date_created')
        except Device.DoesNotExist:
            return

    @property
    def username(self):
        # NOTE: needed for tavern tests
        return self.get_username()

    @property
    def device_token(self) -> Optional[str]:
        last_device = self.last_device
        if last_device:
            return last_device.registration_id

    def __unicode__(self):
        return self.user_UUID

    def get_identicon(self):
        file_path = settings.MEDIA_ROOT + "/identicons/" + self.user_UUID + ".png"
        if not os.path.exists(file_path):
            generator = pydenticon.Generator(5, 5, foreground=settings.IDENTICON_FOREGROUNDS)
            identicon_png = generator.generate(self.user_UUID, 200, 200, output_format="png")
            f = open(file_path, "wb")
            f.write(identicon_png)
            f.close()
        return settings.MEDIA_URL + "identicons/" + self.user_UUID + ".png"

    def update_score(self, commit: bool = True) -> None:
        # NOTE: placing import here due to circular import
        from tigascoring.xp_scoring import compute_user_score_in_xp_v2

        score_dict = compute_user_score_in_xp_v2(user_uuid=self.pk)
        self.score_v2_struct = score_dict

        try:
            self.score_v2_adult = score_dict['score_detail']['adult']['score']
        except (KeyError, TypeError):
            self.score_v2_adult = 0

        try:
            self.score_v2_bite = score_dict['score_detail']['bite']['score']
        except (KeyError, TypeError):
            self.score_v2_bite = 0

        try:
            self.score_v2_site = score_dict['score_detail']['site']['score']
        except (KeyError, TypeError):
            self.score_v2_site = 0

        self.score_v2 = sum([self.score_v2_adult, self.score_v2_bite, self.score_v2_site])
        self.last_score_update = timezone.now()

        if commit:
            self.save()

    def save(self, *args, **kwargs):

        if self.locale:
            self.locale = closest_supported_match(
                self.locale,
                [code for code, _ in self.AVAILABLE_LANGUAGES]
            ) or 'en'

        result = super().save(*args, **kwargs)

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
            language_topic = NotificationTopic.objects.get(topic_code=self.locale)
        except NotificationTopic.DoesNotExist:
            pass
        else:
            UserSubscription.objects.get_or_create(
                user=self,
                topic=language_topic
            )

        return result

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class MobileApp(models.Model):
    package_name = models.CharField(max_length=128)
    package_version = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['package_name', 'package_version'],
                name='unique_name_version',
            )
        ]

    def __str__(self):
        return f'{self.package_name} ({self.package_version})'


class Device(AbstractFCMDevice):
    # NOTE: self.active : If the FCM TOKEN is active
    #       self.is_logged_in : If the Device is is_logged_in for the user

    # NOTE: if ever work on a logout method, set is_logged_in/active to False on logout.
    # Override user to make FK to TigaUser instead of User
    user = models.ForeignKey(
        TigaUser,
        on_delete=models.CASCADE,
        related_name="devices",
        related_query_name=_("fcmdevice"),
    )

    mobile_app = models.ForeignKey(MobileApp, null=True, on_delete=models.PROTECT)
    is_logged_in = models.BooleanField(default=False)

    registration_id = models.TextField(null=True, db_index=True, verbose_name='Registration token')

    manufacturer = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="The manufacturer of the device."
    )
    model = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text="The end-user-visible name for the end product."
    )
    type = models.CharField(choices=DeviceType.choices, max_length=10, null=True)
    os_name = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Operating system of device from which this report was submitted.",
    )
    os_version = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text="Operating system version of device from which this report was submitted.",
    )
    os_locale = models.CharField(
        max_length=16,
        validators=[language_tag_is_valid],
        null=True,
        blank=True,
        help_text="The locale configured in the device following the BCP 47 standard in 'language' or 'language-region' format (e.g., 'en' for English, 'en-US' for English (United States), 'fr' for French). The language is a two-letter ISO 639-1 code, and the region is an optional two-letter ISO 3166-1 alpha-2 code."
    )

    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True)

    history = HistoricalRecords(
        # Exclude field the user can not modify or that are not relevant.
        excluded_fields=[
            'name',
            'date_created',
            'updated_at',
            'is_logged_in',
            'last_login',
            'user'
        ],
        cascade_delete_history=True,
        user_model=TigaUser
    )

    objects = DeviceManager()

    __history_user = None
    @property
    def _history_user(self):
        return self.__history_user or self.user

    @_history_user.setter
    def _history_user(self, value):
        # TODO: if value is uuid, try getting the TigaUser.
        if isinstance(value, TigaUser):
            self.__history_user = value

    def __get_changed_fields(self, update_fields=None):
        if not self.pk:
            return []  # New instance, no changes

        original = self.__class__.objects.get(pk=self.pk)
        changed_fields = []
        for field in self._meta.fields:
            field_name = field.name
            if update_fields and field not in update_fields:
                continue
            if getattr(self, field_name) != getattr(original, field_name):
                changed_fields.append(field_name)

        return changed_fields

    def save(self, *args, **kwargs):
        if self.os_locale:
            self.os_locale = standarize_language_tag(self.os_locale)

        _fields_with_changes = self.__get_changed_fields(update_fields=kwargs.get('update_fields'))
        if self.registration_id and 'registration_id' in _fields_with_changes:
            self.active = True

        if not self.registration_id or not self.is_logged_in:
            self.active = False

        if self.active and self.registration_id:
            update_device_qs = Device.objects.filter(active=True, registration_id=self.registration_id)
            if self.pk:
                update_device_qs = update_device_qs.exclude(pk=self.pk)

            for device in update_device_qs.iterator():
                device.active = False
                # For simple history
                device._change_reason = 'Another user has created/update a device with the same registration_id'
                device.save()

        if self.is_logged_in and self.device_id:
            update_device_qs = Device.objects.filter(is_logged_in=True, device_id=self.device_id)
            if self.pk:
                update_device_qs = update_device_qs.exclude(pk=self.pk)

            for device in update_device_qs.iterator():
                device.is_logged_in = False
                # For simple history
                device._change_reason = 'Another user has created/update a device with the same device_id'
                device.save()

        if self.pk:
            _tracked_fields = [field.name for field in self.__class__.history.model._meta.get_fields()]
            if not any(element in _tracked_fields for element in _fields_with_changes):
                # Only will create history if at least one tracked field has changed.
                self.skip_history_when_saving = True

        try:
            ret = super().save(*args, **kwargs)
        finally:
            if hasattr(self, 'skip_history_when_saving'):
                del self.skip_history_when_saving

        return ret

    def __str__(self):
        # NOTE: this is an override from the inherited class.
        # Never use attributes present in the history.excluded_fields.
        return str(self.pk)

    class Meta(AbstractFCMDevice.Meta):
        abstract = False
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")
        indexes = [
            models.Index(fields=['device_id', 'user']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['registration_id'],
                name='unique_active_registration_id',
                condition=models.Q(active=True) & ~models.Q(registration_id=None) & ~models.Q(registration_id__exact=''),
            ),
            models.UniqueConstraint(
                fields=['device_id'],
                name='unique_is_logged_in_device_id',
                condition=models.Q(is_logged_in=True) & ~models.Q(device_id=None) & ~models.Q(device_id__exact=''),
            ),
            models.UniqueConstraint(
                fields=['user', 'device_id'],
                name='unique_user_device_id',
                condition=models.Q(user__isnull=False, device_id__isnull=False) & ~models.Q(device_id__exact='')
            ),
            models.UniqueConstraint(
                fields=['user', 'registration_id'],
                name='unique_user_registration_id',
                condition=models.Q(user__isnull=False, registration_id__isnull=False) & ~models.Q(registration_id__exact='')
            )
        ]

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
        return self.expiration_time >= datetime.utcnow().replace(tzinfo=timezone.utc)


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
    gid = models.AutoField(primary_key=True)
    cntr_id = models.CharField(max_length=2, blank=True)
    name_engl = models.CharField(max_length=44, help_text='Full name of the country in English (e.g., Spain).')
    iso3_code = models.CharField(max_length=3, help_text='ISO 3166-1 alpha-3 country code (3-letter code, e.g., ESP).')
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

class GlobalAssignmentStat(models.Model):
    country = models.OneToOneField('tigaserver_app.EuropeCountry', primary_key=True, on_delete=models.CASCADE, )
    unassigned_reports = models.IntegerField(default=0)
    in_progress_reports = models.IntegerField(default=0)
    pending_reports = models.IntegerField(default=0)
    nsqueue_reports = models.IntegerField(default=0)
    last_update = models.DateTimeField(help_text="Last time stats were updated", null=True, blank=True)

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

class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    # NOTE: legacy since Report.version_UUID is still a charfield.
    object_id = models.CharField(max_length=36, verbose_name=_("object ID"), db_index=True)

    # See: https://django-taggit.readthedocs.io/en/stable/custom_tagging.html
    class Meta(GenericUUIDTaggedItemBase.Meta, TaggedItemBase.Meta):
        abstract = False

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
        default=uuid.uuid4,
        max_length=36,
        help_text="UUID randomly generated on phone to identify each unique report version. Must be exactly 36 characters (32 hex digits plus 4 hyphens).",
    )
    version_number = models.SmallIntegerField(
        default=0,
        db_index=True,
        editable=False,
        help_text='-1 if deleted, otherwise 0.'
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
        db_index=True,
        help_text="Date and time on server when report uploaded. (Automatically generated by server.)",
    )
    phone_upload_time = models.DateTimeField(
        editable=False,
        help_text="Date and time on phone when it uploaded fix. Format as ECMA 262 date time string (e.g. '2014-05-17T12:34:56.123+01:00'."
    )
    creation_time = models.DateTimeField(
        editable=False,
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
    timezone = TimeZoneField(
        null=True,
        help_text="The timezone corresponding to the GPS of the report."
    )
    location_is_masked = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True, blank=True, editable=False, default=None)

    note = models.TextField(
        null=True, blank=True, help_text="Note user attached to report."
    )

    nuts_2 = models.CharField(max_length=4, null=True, blank=True)
    nuts_3 = models.CharField(max_length=5, null=True, blank=True)

    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_("A comma-separated list of tags you can add to a report to make them easier to find."),
    )

    cached_visible = models.IntegerField(
        null=True, blank=True, help_text="Precalculated value of show_on_map_function"
    )

    mobile_app = models.ForeignKey(
        MobileApp,
        null=True,
        on_delete=models.PROTECT,
        related_name='reports',
        help_text='The mobile app version from where the report was sent.'
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

    # NOTE: if every use django-simplehistory >= 3.1.0, consider using HistoricForeignKey
    device = models.ForeignKey(Device, null=True, on_delete=models.PROTECT, related_name="created_reports", help_text='The device from where the report was sent.')
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

    flipped = models.BooleanField(
        default=False,
        help_text="If true, indicates that the report type has been changed in the coarse filter",
    )

    flipped_on = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of when the report was flipped",
    )

    flipped_to = models.CharField(
        max_length=60,
        null=True,
        blank=True,
        help_text="Type it was flipped from, to type it was flipped to, separated by #"
        '''        
            For instance, if the report was and adult and flipped to storm_drain_water, this field would have the value adult#storm_drain_water
        '''
    )

    # Attributes - user responses - Optional
    EVENT_ENVIRONMENT_INDOORS = 'indoors'
    EVENT_ENVIRONMENT_OUTDOORS = 'outdoors'
    EVENT_ENVIRONMENT_VEHICLE = 'vehicle'

    EVENT_ENVIRONMENT_CHOICES = (
        (EVENT_ENVIRONMENT_INDOORS, _("Indoors")),
        (EVENT_ENVIRONMENT_OUTDOORS, _("Outdoors")),
        (EVENT_ENVIRONMENT_VEHICLE, _("Inside vehicle")),
    )

    event_environment = models.CharField(
        max_length=16, choices=EVENT_ENVIRONMENT_CHOICES, null=True, blank=True,
        help_text=_("The environment where the event took place.")
    )

    EVENT_MOMENT_NOW = 'now'
    EVENT_MOMENT_LAST_MORNING = 'last_morning'
    EVENT_MOMENT_LAST_MIDDAY = 'last_midday'
    EVENT_MOMENT_LAST_AFTERNOON = 'last_afternoon'
    EVENT_MOMENT_LAST_NIGHT = 'last_night'
    EVENT_MOMENT_CHOICES = (
        (EVENT_MOMENT_NOW, _("Now")),
        (EVENT_MOMENT_LAST_MORNING, _("Last morning")),
        (EVENT_MOMENT_LAST_MIDDAY, _("Last midday")),
        (EVENT_MOMENT_LAST_AFTERNOON, _("Last afternoon")),
        (EVENT_MOMENT_LAST_NIGHT, _("Last night")),
    )

    event_moment = models.CharField(
        max_length=32, choices=EVENT_MOMENT_CHOICES, null=True, blank=True,
        help_text=_("The moment of the day when the event took place.")
    )

    bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True, editable=False,
        help_text=_("Total number of bites reported.")
    )

    head_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the head.")
    )
    left_arm_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the left arm.")
    )
    right_arm_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the right arm.")
    )
    chest_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the chest.")
    )
    left_leg_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the left leg.")
    )
    right_leg_bite_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text=_("Number of bites reported in the right leg.")
    )

    SPECIE_ALBOPICTUS = "albopictus"
    SPECIE_AEGYPTI = "aegypti"
    SPECIE_JAPONICUS = "japonicus"
    SPECIE_KOREICUS = "koreicus"
    SPECIE_CULEX = "culex"
    SPECIE_OTHER = "other"

    MOSQUITO_SPECIE_CHOICES = (
        (SPECIE_ALBOPICTUS, "Aedes albopictus"),
        (SPECIE_AEGYPTI, "Aedes aegypti"),
        (SPECIE_JAPONICUS, "Aedes japonicus"),
        (SPECIE_KOREICUS, "Aedes koreicus"),
        (SPECIE_CULEX, "Culex pipiens"),
        (SPECIE_OTHER, _("Other")),
    )

    user_perceived_mosquito_specie = models.CharField(
        max_length=16, choices=MOSQUITO_SPECIE_CHOICES, null=True, blank=True,
        help_text=_("The mosquito specie perceived by the user.")
    )

    user_perceived_mosquito_thorax = models.CharField(
        max_length=16, choices=MOSQUITO_SPECIE_CHOICES, null=True, blank=True,
        help_text=_("The species of mosquito that the thorax resembles, according to the user.")
    )
    user_perceived_mosquito_abdomen = models.CharField(
        max_length=16, choices=MOSQUITO_SPECIE_CHOICES, null=True, blank=True,
        help_text=_("The species of mosquito that the abdomen resembles, according to the user.")
    )
    user_perceived_mosquito_legs = models.CharField(
        max_length=16, choices=MOSQUITO_SPECIE_CHOICES, null=True, blank=True,
        help_text=_("The species of mosquito that the leg resembles, according to the user.")
    )

    BREEDING_SITE_TYPE_BASIN = 'basin'
    BREEDING_SITE_TYPE_BUCKET = 'bucket'
    BREEDING_SITE_TYPE_FOUNTAIN = 'fountain'
    BREEDING_SITE_TYPE_SMALL_CONTAINER = 'small_container'
    BREEDING_SITE_TYPE_STORM_DRAIN = 'storm_drain'
    BREEDING_SITE_TYPE_WELL = 'well'
    BREEDING_SITE_TYPE_OTHER = 'other'

    BREEDING_SITE_TYPE_CHOICES = (
        (BREEDING_SITE_TYPE_BASIN, _('Basin')),
        (BREEDING_SITE_TYPE_BUCKET, _('Bucket')),
        (BREEDING_SITE_TYPE_FOUNTAIN, _('Fountain')),
        (BREEDING_SITE_TYPE_SMALL_CONTAINER, _('Small container')),
        (BREEDING_SITE_TYPE_STORM_DRAIN, _('Storm Drain')),
        (BREEDING_SITE_TYPE_WELL, _('Well')),
        (BREEDING_SITE_TYPE_OTHER, _('Other'))
    )

    breeding_site_type = models.CharField(
        max_length=32, choices=BREEDING_SITE_TYPE_CHOICES, null=True, blank=True,
        help_text=_("Breeding site type.")
    )
    breeding_site_has_water = models.BooleanField(
        null=True, blank=True,
        help_text=_("Either if the user perceived water in the breeding site.")
    )
    breeding_site_in_public_area = models.BooleanField(
        null=True, blank=True,
        help_text=_("Either if the breeding site is found in a public area.")
    )
    breeding_site_has_near_mosquitoes = models.BooleanField(
        null=True, blank=True,
        help_text=_("Either if the user perceived mosquitoes near the breeding site (less than 10 meters).")
    )
    breeding_site_has_larvae = models.BooleanField(
        null=True, blank=True,
        help_text=_("Either if the user perceived larvaes the breeding site.")
    )
    # Object Manager
    objects = ReportManager()

    history = HistoricalRecords(
        # Exclude field the user can not modify or that are not relevant.
        excluded_fields=[
            'user',
            'mission',
            'country',
            'session',
            'version_number',
            'updated_at',
            'server_upload_time',
            'phone_upload_time',
            'version_time',
            'deleted_at',
            'hide',
            'cached_visible',
            'package_name',
            'device_manufacturer',
            'device_model',
            'os',
            'os_version',
            'os_language',
            'app_language',
            'flipped',
            'flipped_on',
            'flipped_to'
        ],
        history_id_field=models.UUIDField(default=uuid.uuid4),
        cascade_delete_history=True, # We are managing deletion through soft-deletions.
        user_model=TigaUser
    )

    __history_user = None
    @property
    def _history_user(self):
        return self.__history_user

    @_history_user.setter
    def _history_user(self, value):
        # TODO: if value is uuid, try getting the TigaUser.
        if isinstance(value, TigaUser):
            self.__history_user = value

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
        return self.deleted_at is not None

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

    @cached_property
    def published(self) -> bool:
        return Report.objects.published().filter(pk=self.pk).exists()

    @property
    def public_map_url(self) -> Optional[str]:
        if not self.published:
            return None
        return f"https://map.mosquitoalert.com/{self.pk}/en"

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
        return self.photos.visible().all()

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
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_BASIN

    @property
    def buckets(self) -> bool:
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_BUCKET

    @property
    def embornals(self) -> bool:
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_STORM_DRAIN

    @property
    def fonts(self) -> bool:
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_FOUNTAIN

    @property
    def other(self) -> bool:
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_OTHER

    @property
    def wells(self) -> bool:
        return self.breeding_site_type == self.BREEDING_SITE_TYPE_WELL

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

    @property
    def creation_time_local(self) -> datetime:
        if self.timezone:
            return self.creation_time.astimezone(self.timezone)
        return self.creation_time

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
        # Forcing self.version_number to be either 0 or -1
        self.version_number = 0 if self.version_number >= 0 else -1

        self.version_time = self.version_time or self.creation_time

        # Recreate the Point (just in case lat/lon has changed)
        _old_point = self.point
        self.point = self._get_point()
        self.timezone = self.get_timezone_from_coordinates()
        if _old_point != self.point:
            _last_location_update = self.user.last_location_update
            _report_upload_time = self.server_upload_time or timezone.now()
            if _last_location_update and _report_upload_time >= _last_location_update:
                self.user.last_location = self.point
                self.user.last_location_update = _report_upload_time
                self.user.save()

        if self.app_language:
            self.app_language = standarize_language_tag(self.app_language)
            self.user.locale = self.app_language
            self.user.save()

        if self.os_language:
            self.os_language = standarize_language_tag(self.os_language)

        if self._state.adding:
            if self.note and not self.tags.exists():
                # Init tags from note hashtags
                self.tags.set(set(re.findall(r'(?<=#)\w+', self.note)))

            # Set mobile_app
            if self.package_name and self.package_version:
                self.mobile_app, _ = MobileApp.objects.get_or_create(
                    package_name=self.package_name,
                    package_version=self.package_version
                )
            # Update device according to the information provided in the report.
            try:
                # Try to update the device created in /token/ legacy api
                # which creates a device with empty fields, except for registration_id.
                device = Device.objects.filter(
                    user=self.user,
                    model__isnull=True,
                    date_created__lte=self.server_upload_time or timezone.now()
                ).latest('date_created')
                device.type={
                    'android': 'android',
                    'ipados': 'ios',
                    'ios': 'ios',
                    'iphone os': 'ios'
                }.get(self.os.lower() if self.os else None)
                device.manufacturer = self.device_manufacturer
                device.model = self.device_model
                device.os_name = self.os
                device.os_version = self.os_version
                device.os_locale = self.os_language
                device.mobile_app = self.mobile_app
                device.is_logged_in = True
                device.last_login = self.server_upload_time or timezone.now()
                device.save()
            except Device.DoesNotExist:
                # Create a new Device.
                device, _ = Device.objects.update_or_create(
                    user=self.user,
                    model=self.device_model,
                    type={
                        'android': 'android',
                        'ipados': 'ios',
                        'ios': 'ios',
                        'iphone os': 'ios'
                    }.get(self.os.lower() if self.os else None),
                    defaults={
                        'is_logged_in': True,
                        'last_login': self.server_upload_time or timezone.now(),
                        'manufacturer': self.device_manufacturer,
                        'model': self.device_model,
                        'os_name': self.os,
                        'os_version': self.os_version,
                        'os_locale': self.os_language,
                        'mobile_app': self.mobile_app
                    }
                )

            self.device = device

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

        if self.point:
            if self.country:
                nuts3 = self._get_nuts_is_in(levl_code=3)
                if nuts3:
                    self.nuts_3 = nuts3.nuts_id

                nuts2 = self._get_nuts_is_in(levl_code=2)
                if nuts2:
                    self.nuts_2 = nuts2.nuts_id
            else:
                # Check if masked because of is in the ocean of out of the artic/antartic circle.
                self.location_is_masked = self.point.y > settings.MAX_ALLOWED_LATITUDE \
                    or self.point.y < settings.MIN_ALLOWED_LATITUDE \
                    or settings.OCEAN_GEOM.contains(self.point)

        bite_fieldnames = [
            'head_bite_count',
            'left_arm_bite_count',
            'right_arm_bite_count',
            'chest_bite_count',
            'left_leg_bite_count',
            'right_leg_bite_count'
        ]

        if self.type == self.TYPE_BITE:
            # Make sure all bites are set to 0 if none.
            for bite_fieldname in bite_fieldnames:
                if getattr(self, bite_fieldname) is None:
                    setattr(self, bite_fieldname, 0)

            self.bite_count = sum(
                getattr(self, fname) for fname in bite_fieldnames
            )

        super(Report, self).save(*args, **kwargs)

        self.user.update_score()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.version_number = -1
        self.save_without_historical_record()

    def restore(self):
        self.deleted_at = None
        self.version_number = 0
        self.save_without_historical_record()

    def delete(self, *args, **kwargs):
        self.user.update_score()
        return super().delete(*args, **kwargs)

    # Meta and String
    class Meta:
        # NOTE: this ordering is prone to bugs, do not uncomment.
        # ordering = ['server_upload_time', ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    version_number=0,
                    deleted_at__isnull=True
                ) | models.Q(
                    version_number=-1,
                    deleted_at__isnull=False
                ),
                name='version_number_constraint'
            )
        ]
        indexes = [
            # NOTE: Improve performance of .views.ReportViewSet
            models.Index(fields=["user", "type", "report_id"])
        ]

    def __unicode__(self):
        return self.pk


    def get_photo_html_for_report_validation_completed(self):
        result = ''
        for photo in self.visible_photos:
            best_photo = ExpertReportAnnotation.objects.filter(best_photo=photo).exists()
            border_style = "3px solid green" if best_photo else "1px solid #333333"
            result += '<div id="' + str(photo.id) + '" style="border: ' + border_style + ';margin:1px;">' + photo.medium_image_for_validation_() + '</div><div>' + get_icon_for_blood_genre(photo.blood_genre) + '</div><br>'
        return result

    def get_crowdcrafting_score(self):
        if self.type not in (self.TYPE_SITE, self.TYPE_ADULT):
            return None
        these_photos = self.photos.visible().annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
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
        these_photos = self.photos.visible().annotate(n_responses=Count('crowdcraftingtask__responses')).filter(n_responses__gte=30)
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
            try:
                most_voted = Categories.objects.get(name='Unclassified')
                retval['in_progress'] = True
            except Categories.DoesNotExist:
                pass

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
                try:
                    retval['category'] = Categories.objects.get(pk=8)
                except Categories.DoesNotExist:
                    pass
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
    return Report.objects.filter(user=user).exclude(type=Report.TYPE_BITE).non_deleted().count()


@receiver(post_save, sender=Report)
def subscribe_user_to_country_topic(sender, instance, created, **kwargs):
    if not created:
        return

    topic_code_candidates = [instance.country, instance.nuts_2, instance.nuts_3]
    for topic_code in filter(lambda x: x is not None, topic_code_candidates):
        try:
            topic = NotificationTopic.objects.get(topic_code=topic_code)
        except NotificationTopic.DoesNotExist:
            pass
        else:
            UserSubscription.objects.get_or_create(
                user=instance.user,
                topic=topic
            )

@receiver(post_save, sender=Report)
def maybe_give_awards(sender, instance, created, **kwargs):
    #only for adults and sites
    if created:
        try:
            super_movelab = User.objects.get(pk=24)
            n_reports = get_user_reports_count(instance.user)
            if n_reports == 10:
                grant_10_reports_achievement(instance, super_movelab)
            if n_reports == 20:
                grant_20_reports_achievement(instance, super_movelab)
            if n_reports == 50:
                grant_50_reports_achievement(instance, super_movelab)
            if instance.type == Report.TYPE_ADULT or instance.type == Report.TYPE_SITE:
                # check award for first of season
                current_year = instance.creation_time.year
                awards = Award.objects.filter(given_to=instance.user).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season')
                if awards.count() == 0:  # not yet awarded
                    # can be first of season?
                    if instance.creation_time.month >= conf.SEASON_START_MONTH and instance.creation_time.day >= conf.SEASON_START_DAY:
                        grant_first_of_season(instance, super_movelab)

                report_day = instance.creation_time.day
                report_month = instance.creation_time.month
                report_year = instance.creation_time.year
                awards = Award.objects \
                    .filter(report__creation_time__year=report_year) \
                    .filter(report__creation_time__month=report_month) \
                    .filter(report__creation_time__day=report_day) \
                    .filter(report__user=instance.user) \
                    .filter(category__category_label='daily_participation').order_by(
                    'report__creation_time')  # first is oldest
                if awards.count() == 0: # not yet awarded
                    grant_first_of_day(instance, super_movelab)

                date_1_day_before_report = instance.creation_time - timedelta(days=1)
                date_1_day_before_report_adjusted = date_1_day_before_report.replace(hour=23, minute=59, second=59)
                report_before_this_one = Report.objects.filter(user=instance.user).filter(creation_time__lte=date_1_day_before_report_adjusted).order_by('-creation_time').first()  # first is most recent
                if report_before_this_one is not None and one_day_between_and_same_week(report_before_this_one.creation_time, instance.creation_time):
                    #report before this one has not been awarded neither 2nd nor 3rd day streak
                    if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count()==0 and Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_3').count()==0:
                        grant_two_consecutive_days_sending(instance, super_movelab)
                    else:
                        if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count() == 1:
                            grant_three_consecutive_days_sending(instance, super_movelab)
        except User.DoesNotExist:
            pass


class ReportResponse(models.Model):
    report = models.ForeignKey(Report, related_name='responses', help_text='Report to which this response is associated.', on_delete=models.CASCADE, )
    question_id = models.IntegerField(blank=True, null=True, help_text='Numeric identifier of the question.')
    question = models.CharField(max_length=1000, help_text='Question that the user responded to.')
    answer_id = models.IntegerField(blank=True, null=True, help_text='Numeric identifier of the answer.')
    answer = models.CharField(max_length=1000, help_text='Answer that user selected.')
    answer_value = models.CharField(max_length=1000, blank=True, null=True, help_text='The value right now can contain 2 things: an integer representing the number or bites, or either a WKT representation of a point for a location answer. In all other cases, it will be blank')

    def _update_report_value(self, commit: bool = True):
        report_obj = self.report

        # Convert the original state of the object to a dictionary
        original_report_state = model_to_dict(report_obj)

        if self.question_id == 2:
            if self.answer_id == 21:
                report_obj.head_bite_count = int(self.answer_value)
            elif self.answer_id == 22:
                report_obj.left_arm_bite_count = int(self.answer_value)
            elif self.answer_id == 23:
                report_obj.right_arm_bite_count = int(self.answer_value)
            elif self.answer_id == 24:
                report_obj.chest_bite_count = int(self.answer_value)
            elif self.answer_id == 25:
                report_obj.left_leg_bite_count = int(self.answer_value)
            elif self.answer_id == 26:
                report_obj.right_leg_bite_count = int(self.answer_value)
        elif self.question_id == 3:
            if self.answer_id == 31:
                report_obj.event_moment = Report.EVENT_MOMENT_LAST_MORNING
            elif self.answer_id == 32:
                report_obj.event_moment = Report.EVENT_MOMENT_LAST_MIDDAY
            elif self.answer_id == 33:
                report_obj.event_moment = Report.EVENT_MOMENT_LAST_AFTERNOON
            elif self.answer_id == 34:
                report_obj.event_moment = Report.EVENT_MOMENT_LAST_NIGHT
        elif self.question_id == 4:
            if self.answer_id == 41:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_VEHICLE
            elif self.answer_id == 42:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_INDOORS
            elif self.answer_id == 43:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_OUTDOORS
            elif self.answer_id == 44:
                report_obj.event_environment = None
        elif self.question_id == 5:
            if self.answer_id == 51:
                report_obj.event_moment = Report.EVENT_MOMENT_NOW
        elif self.question == 'question_6':
            # NOTE: using question since question_id '6' not present in DB.
            if self.answer_id == 61:
                report_obj.user_perceived_mosquito_specie = Report.SPECIE_ALBOPICTUS
            elif self.answer_id == 62:
                report_obj.user_perceived_mosquito_specie = Report.SPECIE_CULEX
            elif self.answer_id == 63:
                report_obj.user_perceived_mosquito_specie = Report.SPECIE_OTHER
            elif self.answer_id == 64:
                report_obj.user_perceived_mosquito_specie = None
        elif self.question_id == 7 or self.question == 'question_7':
            # Thorax
            if self.answer_id == 711:
                report_obj.user_perceived_mosquito_thorax = Report.SPECIE_ALBOPICTUS
            elif self.answer_id == 712:
                report_obj.user_perceived_mosquito_thorax = Report.SPECIE_AEGYPTI
            elif self.answer_id == 713:
                report_obj.user_perceived_mosquito_thorax = Report.SPECIE_JAPONICUS
            elif self.answer_id == 714:
                report_obj.user_perceived_mosquito_thorax = Report.SPECIE_KOREICUS

            # Abdomen
            if self.answer_id == 721:
                report_obj.user_perceived_mosquito_abdomen = Report.SPECIE_ALBOPICTUS
            elif self.answer_id == 722:
                report_obj.user_perceived_mosquito_abdomen = Report.SPECIE_AEGYPTI
            elif self.answer_id == 723:
                report_obj.user_perceived_mosquito_abdomen = Report.SPECIE_JAPONICUS
            elif self.answer_id == 724:
                report_obj.user_perceived_mosquito_abdomen = Report.SPECIE_KOREICUS

            # Legs
            if self.answer_id == 731:
                report_obj.user_perceived_mosquito_legs = Report.SPECIE_ALBOPICTUS
            elif self.answer_id == 732:
                report_obj.user_perceived_mosquito_legs = Report.SPECIE_AEGYPTI
            elif self.answer_id == 733:
                report_obj.user_perceived_mosquito_legs = Report.SPECIE_JAPONICUS
            elif self.answer_id == 734:
                report_obj.user_perceived_mosquito_legs = Report.SPECIE_KOREICUS
        elif self.question_id == 10:
            if self.answer_id == 81 or self.answer_id == 102:
                report_obj.breeding_site_has_water = False
            elif self.answer_id == 101:
                report_obj.breeding_site_has_water = True
        elif self.question_id == 12:
            if self.answer_id == 121:
                report_obj.breeding_site_type = Report.BREEDING_SITE_TYPE_STORM_DRAIN
            elif self.answer_id == 122:
                report_obj.breeding_site_type = Report.BREEDING_SITE_TYPE_OTHER
        elif self.question_id == 13:
            if self.answer_id == 131:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_VEHICLE
            elif self.answer_id == 132:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_INDOORS
            elif self.answer_id == 133:
                report_obj.event_environment = Report.EVENT_ENVIRONMENT_OUTDOORS
        elif self.question_id == 17:
            if self.answer_id == 81 or self.answer_id == 102:
                self.breeding_site_has_water = False
            elif self.answer_id == 101:
                self.breeding_site_has_water = True

        # Check if any field has changed
        if commit and any(getattr(report_obj, field) != original_report_state[field] for field in original_report_state.keys()):
            # Save the object only if there are changes, not to trigger auto_now fields.
            report_obj.save()

    def save(self, skip_report_update: bool = False, *args, **kwargs):
        # NOTE: this is needed to ensure question_id/answer_id are integers.
        #       _update_report_value works as expected.
        if self.question_id is not None:
            self.question_id = int(self.question_id)

        if self.answer_id is not None:
            self.answer_id = int(self.answer_id)

        super().save(*args, **kwargs)

        if not skip_report_update:
            self._update_report_value()

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

BLOOD_GENRE = (('male', 'Male'), ('female', 'Female'), ('fblood', 'Female blood'), ('fgravid', 'Female gravid'), ('fgblood', 'Female gravid + blood'), ('dk', 'Dont know') )

class Photo(models.Model):
    """
    Photo uploaded by user.
    """
    photo = ProcessedImageField(
        upload_to=make_image_uuid,
        processors=[ResizeToFit(height=2160, upscale=False)],
        format="JPEG",
        options={"quality": 98},
        help_text='Photo uploaded by user.'
    )
    report = models.ForeignKey(Report, related_name='photos', help_text='Report and version to which this photo is associated (36-digit '
                                                 'report_UUID).', on_delete=models.CASCADE, )
    hide = models.BooleanField(default=False, help_text='Hide this photo from public views?', db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    blood_genre = models.CharField(max_length=20, choices=BLOOD_GENRE, null=True, default=None)

    objects = PhotoManager()

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
                    im.thumbnail((120, 120))
                    im.save(self.get_small_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_small/')
        return self.photo.url

    def get_popup_url(self):
        if os.path.isfile(self.photo.path):
            if not os.path.isfile(self.get_popup_path()):
                try:
                    im = Image.open(self.photo.path)
                    im.thumbnail((180, 180))
                    im.save(self.get_popup_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_popups/')
        return self.photo.url

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
                    im.thumbnail((460, 460))
                    im.save(self.get_medium_path())
                except IOError:
                    return ""
            return self.photo.url.replace('tigapics/', 'tigapics_medium/')
        return self.photo.url

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

    GRID_SIZE = 0.025

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
    masked_lon = models.FloatField(help_text=f'Longitude rounded down to nearest {GRID_SIZE} decimal degree.')
    masked_lat = models.FloatField(help_text=f'Latitude rounded down to nearest {GRID_SIZE} decimal degree.')
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

    def save(self, *args, **kwargs):
        # Force masking of lat/lon
        self.masked_lon = round(floor(self.masked_lon / self.GRID_SIZE) * self.GRID_SIZE, 5)
        self.masked_lat = round(floor(self.masked_lat / self.GRID_SIZE) * self.GRID_SIZE, 5)

        super().save(*args, **kwargs)

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
        body = soup.find('body')  # Try to find the <body> tag
        if body:
            return body.get_text(separator='\n', strip=True)  # If <body> is found, extract text
        else:
            # If no <body> tag is found, return text from the entire HTML document
            return soup.get_text(separator='\n', strip=True)

    def save(self, *args, **kwargs):
        if not (self.title_native and self.body_html_native):
            self.native_locale = None
        super().save(*args, **kwargs)

class Notification(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', null=True, blank=True, related_name='report_notifications', help_text='Report regarding the current notification', on_delete=models.CASCADE, )
    # The field 'user' is kept for backwards compatibility with the map notifications. It only has meaningful content on MAP NOTIFICATIONS
    # and in all other cases is given a default value (null user 00000000-0000-0000-0000-000000000000)
    user = models.ForeignKey(TigaUser, null=True, blank=True, on_delete=models.CASCADE)
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

    objects = NotificationManager()

    def mark_as_seen_for_user(self, user: TigaUser) -> None:
        _ = AcknowledgedNotification.objects.get_or_create(
            user=user,
            notification=self
        )

    def mark_as_unseen_for_user(self, user: TigaUser) -> None:
        _ = AcknowledgedNotification.objects.filter(
            user=user,
            notification=self
        ).delete()


    def send_to_topic(self, topic: 'NotificationTopic', push: bool = True, language_code: Optional[str] = None) -> Optional[SendResponse]:
        obj, _ = SentNotification.objects.get_or_create(
            sent_to_topic=topic,
            notification=self
        )

        if push:
            return obj.send_push(language_code=language_code)

    def send_to_user(self, user: TigaUser, push: bool = True) -> Optional[BatchResponse]:
        obj, _ = SentNotification.objects.get_or_create(
            sent_to_user=user,
            notification=self
        )

        if push:
            return obj.send_push(language_code=user.locale)

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
        if self._state.adding:
            try:
                self.user.devices.all().handle_topic_subscription(
                    should_subscribe=True, # Subscribe
                    topic=self.topic.topic_code,
                )
            except ValueError as e:
                logger_notification.exception(str(e))

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        try:
            self.user.devices.all().handle_topic_subscription(
                should_subscribe=False,  # Unsubscribe
                topic=self.topic.topic_code,
            )
        except ValueError as e:
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

    def send_push(self, language_code: str = None) -> Union[SendResponse, BatchResponse]:

        if settings.DISABLE_PUSH:
            return

        # See: https://firebase.google.com/docs/reference/admin/python/firebase_admin.messaging
        # See: https://firebaseopensource.com/projects/flutter/plugins/packages/firebase_messaging/readme/
        message = Message(
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

        try:
            if self.sent_to_topic:
                return Device.send_topic_message(
                    message=message,
                    topic_name=self.sent_to_topic.topic_code
                )
            elif self.sent_to_user:
                return self.sent_to_user.devices.all().send_message(
                    message=message
                ).response
        except (FirebaseError, ValueError) as e:
            logger_notification.exception(str(e))
        except Exception as e:
            logger_notification.exception(str(e))


class AwardCategory(models.Model):
    category_label = models.TextField(help_text='Coded label for the translated version of the award. For instance award_good_picture. This code refers to strings in several languages')
    xp_points = models.IntegerField(help_text='Number of xp points associated to this kind of award')
    category_long_description = models.TextField(default=None, blank=True, null=True, help_text='Long description specifying conditions in which the award should be conceded')


class Award(models.Model):
    report = models.ForeignKey('tigaserver_app.Report', default=None, blank=True, null=True, related_name='report_award', help_text='Report which the award refers to. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    date_given = models.DateTimeField(default=datetime.now, help_text='Date in which the award was given')
    given_to = models.ForeignKey(TigaUser, related_name="user_awards", help_text='User to which the notification was awarded. Usually this is the user that uploaded the report, but the report can be blank for special awards', on_delete=models.CASCADE, )
    expert = models.ForeignKey(User, null=True, blank=True, related_name="expert_awards", help_text='Expert that gave the award', on_delete=models.SET_NULL, )
    category = models.ForeignKey(AwardCategory, blank=True, null=True, related_name="category_awards", help_text='Category to which the award belongs. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    special_award_text = models.TextField(default=None, blank=True, null=True, help_text='Custom text for custom award')
    special_award_xp = models.IntegerField(default=0, blank=True, null=True, help_text='Custom xp awarded')

    def save(self, *args, **kwargs) -> None:
        is_adding = self._state.adding

        super().save(*args, **kwargs)

        if is_adding:
            send_new_award_notification(award=self)

        if self.given_to is not None:
            self.given_to.update_score()

    def delete(self, *args, **kwargs):
        if self.given_to is not None:
            self.given_to.update_score()

        return super().delete(*args, **kwargs)

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


class PhotoClassifierScoresMeta(ModelBase):
    CLASS_FIELDNAMES_CHOICES = [
        ('ae_albopictus', "Aedes albopictus"),
        ('ae_aegypti', "Aedes aegypti"),
        ('ae_japonicus', "Aedes japonicus"),
        ('ae_koreicus', "Aedes koreicus"),
        ('culex', "Culex (s.p)"),
        ('anopheles', "Anopheles (s.p.)"),
        ('culiseta', "Culiseta (s.p.)"),
        ('other_species', "Ohter species"),
        ('not_sure', "Unidentifiable")
    ]
    CLASS_UNCLASSIFIED = "not_sure"
    CLASS_FIELD_SUFFIX = "_score"

    def __new__(cls, name, bases, attrs, **kwargs):
        # Dynamically create FloatFields for each classifier result
        for fname, value in cls.CLASS_FIELDNAMES_CHOICES:
            # Apply suffix to the field names (will be overridden in subclasses)
            field_name = f'{fname}{cls.CLASS_FIELD_SUFFIX or ""}'
            attrs[field_name] = models.FloatField(
                validators=[
                    MinValueValidator(0.0),
                    MaxValueValidator(1.0)
                ],
                help_text=f"Score value for the class {value}"
            )
        return super().__new__(cls, name, bases, attrs, **kwargs)

class PhotoPrediction(models.Model, metaclass=PhotoClassifierScoresMeta):

    CLASSIFIER_VERSION_CHOICES = [
        ('v2023.1', 'v2023.1'),
        ('v2024.1', 'v2024.1'),
        ('v2025.1', 'v2025.1'),
    ]

    PREDICTED_CLASS_TO_CATEGORY = {
            'ae_aegypti': 5,
            'ae_albopictus': 4,
            'anopheles': 2,
            'culex': 10,
            'culiseta': 2,
            'ae_japonicus': 6,
            'ae_koreicus': 7,
            'other_species': 2,
            'not_sure': 9,
        }

    PREDICTED_CLASS_TO_OTHERSPECIES = {
        'anopheles': 101,
        'culiseta': 103
    }

    @classmethod
    def get_score_fieldnames(cls):
        return [fname + cls.CLASS_FIELD_SUFFIX for fname, _ in cls.CLASS_FIELDNAMES_CHOICES]

    photo = models.OneToOneField(Photo, primary_key=True, related_name='prediction', help_text='Photo to which the score refers to', on_delete=models.CASCADE, limit_choices_to={"report__type": Report.TYPE_ADULT})

    classifier_version = models.CharField(max_length=16, choices=CLASSIFIER_VERSION_CHOICES)

    insect_confidence = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ],
        help_text='Insect confidence'
    )

    predicted_class = models.CharField(max_length=32, choices=PhotoClassifierScoresMeta.CLASS_FIELDNAMES_CHOICES, default=PhotoClassifierScoresMeta.CLASS_UNCLASSIFIED)
    threshold_deviation = models.FloatField(
        validators=[
            MinValueValidator(-1.0),
            MaxValueValidator(1.0)
        ],
    )

    x_tl = models.PositiveIntegerField(help_text="photo bounding box coordinates top left x")
    x_br = models.PositiveIntegerField(help_text="photo bounding box coordinates bottom right x")
    y_tl = models.PositiveIntegerField(help_text="photo bounding box coordinates top left y")
    y_br = models.PositiveIntegerField(help_text="photo bounding box coordinates bottom right y")

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    @property
    def category_id(self):
        return self.PREDICTED_CLASS_TO_CATEGORY.get(self.predicted_class)

    @property
    def otherspecies_id(self):
        return self.PREDICTED_CLASS_TO_OTHERSPECIES.get(self.predicted_class)

    def clean(self):
        # Get the linked photo dimensions
        try:
            width, height = self.photo.photo.width, self.photo.photo.height
        except FileNotFoundError:
            width = height = None

        # Check if x_br is greater than the photo width
        if width is not None and self.x_br > width:
            raise ValidationError("Bottom right x-coordinate (x_br) cannot exceed the width of the photo.")

        # Check if y_br is greater than the photo height
        if height is not None and self.y_br > height:
            raise ValidationError("Bottom right y-coordinate (y_br) cannot exceed the height of the photo.")

    def save(self, *args, **kwargs):
        self.clean()

        super().save(*args, **kwargs)

        try:
            # On update update expert report annotation.
            ObservationPrediction.objects.get(photo_prediction=self).update_expert_annotation()
        except ObservationPrediction.DoesNotExist:
            pass

    class Meta:
        constraints = [
            # Ensure x_tl is less than or equal to x_br
            models.CheckConstraint(
                check=Q(x_tl__lte=models.F('x_br')),
                name='x_tl_less_equal_x_br'
            ),
            # Ensure y_tl is less than or equal to y_br
            models.CheckConstraint(
                check=Q(y_tl__lte=models.F('y_br')),
                name='y_tl_less_equal_y_br'
            ),
        ]

class ObservationPrediction(models.Model):

    report = models.OneToOneField(Report, primary_key=True, related_name='prediction', on_delete=models.CASCADE, limit_choices_to={"report__type": Report.TYPE_ADULT})
    photo_prediction = models.OneToOneField(PhotoPrediction, on_delete=models.CASCADE)

    expert_annotation = models.ForeignKey(
        ExpertReportAnnotation, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text='Linked expert annotation created after setting this prediction to be used a executive validation.'
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def _get_public_message(self):
        public_message = f"Our AI identified the mosquito in this photo as {self.photo_prediction.get_predicted_class_display()}. Thanks for participating!"
        if self.photo_prediction.predicted_class == PhotoPrediction.CLASS_UNCLASSIFIED:
            public_message = "Our AI has processed this image but it is not confident enough to identify the mosquito species (the score is below our threshold of confidence). Still, your observation is very useful. Thanks for participating!"

        return public_message

    def create_executive_expert_annotation(self):
        # AI can only create if nobody has validated..
        if ExpertReportAnnotation.objects.filter(report=self.report).exists():
            return

        self.expert_annotation = ExpertReportAnnotation.objects.create(
            user=User.objects.get(username='aima'),
            report=self.report,
            best_photo=self.photo_prediction.photo,
            category_id=self.photo_prediction.category_id,
            other_species=self.photo_prediction.otherspecies_id,
            validation_value=ExpertReportAnnotation.VALIDATION_CATEGORY_PROBABLY,
            validation_complete=True,
            validation_complete_executive=True,
            simplified_annotation=False,
            status=1,  # Force public
            edited_user_notes=self._get_public_message(),
        )
        self.save()

    def update_expert_annotation(self):
        if not self.expert_annotation:
            return

        expert_annotation = self.expert_annotation

        expert_annotation.best_photo=self.photo_prediction.photo
        expert_annotation.category_id=self.photo_prediction.category_id
        expert_annotation.other_species=self.photo_prediction.otherspecies_id
        expert_annotation.edited_user_notes=self._get_public_message()
        expert_annotation.save()

    def delete(self, *args, **kwargs):
        if self.expert_annotation:
            self.expert_annotation.delete()

        return super().delete(*args, **kwargs)
