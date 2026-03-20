from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Message, Notification as FirebaseNotification, AndroidConfig, AndroidNotification, SendResponse, BatchResponse
import logging
from math import floor
from PIL import Image
import os
import random
import string
from typing import List, Optional, Union
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model

from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import Distance as DistanceMeasure
from django.core.validators import RegexValidator
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from fcm_django.models import AbstractFCMDevice, DeviceType
from imagekit.processors import ResizeToFit
from langcodes import standardize_tag as standarize_language_tag, tag_is_valid as language_tag_is_valid
from semantic_version import Version
from semantic_version.django_fields import VersionField
from simple_history.models import HistoricalRecords
from timezone_field import TimeZoneField
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

from mosquito_alert.geo.models import EuropeCountry, NutsEurope, LauEurope
from mosquito_alert.identification_tasks.models import IdentificationTask
from mosquito_alert.users.models import TigaUser

from .fields import ProcessedImageField
from .managers import ReportManager, PhotoManager, NotificationManager, DeviceManager
from .mixins import TimeZoneModelMixin

logger_report_geolocation = logging.getLogger('mosquitoalert.location.report_location')
logger_notification = logging.getLogger('mosquitoalert.notification')

User = get_user_model()



class MobileApp(models.Model):
    # NOTE: At some point we should adjust the package_version which 'build' value is 'legacy'
    #       since this version were creating from Report.package_version (which is an IntegerField)
    #       and it's a number which is not related with the Mobile App pubspeck.yaml package version.
    package_name = models.CharField(max_length=128)
    package_version = VersionField(max_length=32, validators=[
        RegexValidator(
            regex=Version.version_re,
            code='invalid_version'
        )
    ])

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
    #       self.active_session : If the Device has and active logged session for the user

    # NOTE: if ever work on a logout method, set active_session/active to False on logout.
    # Override user to make FK to TigaUser instead of User
    user = models.ForeignKey(
        TigaUser,
        on_delete=models.CASCADE,
        related_name="devices",
        related_query_name=_("fcmdevice"),
    )

    mobile_app = models.ForeignKey(MobileApp, null=True, on_delete=models.PROTECT)
    active_session = models.BooleanField(default=False)

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
            'active_session',
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

        self.active = bool(self.registration_id and self.active_session)

        if self.active and self.registration_id:
            update_device_qs = Device.objects.filter(active=True, registration_id=self.registration_id)
            if self.pk:
                update_device_qs = update_device_qs.exclude(pk=self.pk)

            for device in update_device_qs.iterator():
                device.active = False
                # For simple history
                device._change_reason = 'Another user has created/update a device with the same registration_id'
                device.save()

        if self.active_session and self.device_id:
            update_device_qs = Device.objects.filter(active_session=True, device_id=self.device_id)
            if self.pk:
                update_device_qs = update_device_qs.exclude(pk=self.pk)

            for device in update_device_qs.iterator():
                device.active_session = False
                # For simple history
                device._change_reason = 'Another user has created/update a device with the same device_id'
                device.save()

        if self.pk:
            _tracked_fields = [field.name for field in self.__class__.history.model._meta.get_fields()]
            _fields_with_changes = self.__get_changed_fields(update_fields=kwargs.get('update_fields'))
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
                fields=['active', 'registration_id'],
                name='unique_active_registration_id',
                condition=models.Q(active=True, registration_id__isnull=False) & ~models.Q(registration_id__exact=''),
            ),
            models.UniqueConstraint(
                fields=['active_session', 'device_id'],
                name='unique_active_session_device_id',
                condition=models.Q(active_session=True, device_id__isnull=False) & ~models.Q(device_id__exact=''),
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

def generate_report_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=4))

class Report(TimeZoneModelMixin, models.Model):
    @staticmethod
    def get_tags_from_note(note: str) -> List[str]:
        return list(set(re.findall(r'(?<=#)\w+', note)))

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
    PUBLISHABLE_TYPES = [TYPE_BITE, TYPE_ADULT, TYPE_SITE]

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
        default=generate_report_id,
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

    published_at = models.DateTimeField(
        editable=False,
        null=True,
        blank=True,
        db_index=True,
        help_text='Datetime when the report was published.'
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
        db_index=True,
        help_text="Type of report: 'adult', 'site', or 'mission'.",
    )

    hide = models.BooleanField(
        default=False, db_index=True, help_text="Hide this report from public views?"
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

    lau_fk = models.ForeignKey(LauEurope, null=True, blank=True, on_delete=models.PROTECT, related_name='+')
    nuts_2_fk = models.ForeignKey(NutsEurope, null=True, blank=True, on_delete=models.PROTECT, related_name='+', limit_choices_to={'levl_code': 2})
    nuts_3_fk = models.ForeignKey(NutsEurope, null=True, blank=True, on_delete=models.PROTECT, related_name='+', limit_choices_to={'levl_code': 3})
    # NOTE: do not remove yet for legacy reasons
    nuts_2 = models.CharField(max_length=4, null=True, blank=True, editable=False)
    nuts_3 = models.CharField(max_length=5, null=True, blank=True, editable=False)

    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
        help_text=_("A comma-separated list of tags you can add to a report to make them easier to find."),
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

    class BreedingSiteType(models.TextChoices):
        BASIN = "basin", _("Basin")
        BUCKET = "bucket", _("Bucket")
        FOUNTAIN = "fountain", _("Fountain")
        SMALL_CONTAINER = "small_container", _("Small container")
        STORM_DRAIN = "storm_drain", _("Storm Drain")
        WELL = "well", _("Well")
        OTHER = "other", _("Other")

    breeding_site_type = models.CharField(
        max_length=32, choices=BreedingSiteType.choices, null=True, blank=True,
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
            'country',
            'session',
            'version_number',
            'updated_at',
            'server_upload_time',
            'phone_upload_time',
            'version_time',
            'deleted_at',
            'hide',
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
    def deleted(self) -> bool:
        return self.deleted_at is not None

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
    def is_browsable(self) -> bool:
        return not (
            self.hide or
            self.deleted or
            self.location_is_masked
        )

    @property
    def published(self) -> bool:
        return self.is_browsable and bool(self.published_at) and self.published_at <= timezone.now()

    @property
    def location_display_name(self) -> Optional[str]:
        result = []
        if self.lau_fk:
            result.append(self.lau_fk.name)
        if self.nuts_3_fk:
            result.append(self.nuts_3_fk.name)
        if self.nuts_2_fk:
            result.append(self.nuts_2_fk.name)
        if self.country:
            result.append(self.country.name_engl)

        if not result:
            return

        return ', '.join(result)

    @property
    def public_map_url(self) -> Optional[str]:
        if not self.published:
            return None
        return f"https://map.mosquitoalert.com/{self.pk}"

    @property
    def visible_photos(self):
        return self.photos.visible().all()

    @property
    def n_visible_photos(self) -> int:
        return self.visible_photos.count()

    # Custom properties related to breeding sites
    @property
    def basins(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.BASIN

    @property
    def buckets(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.BUCKET

    @property
    def embornals(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.STORM_DRAIN

    @property
    def fonts(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.FOUNTAIN

    @property
    def other(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.OTHER

    @property
    def wells(self) -> bool:
        return self.breeding_site_type == Report.BreedingSiteType.WELL

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

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Forcing self.version_number to be either 0 or -1
        self.version_number = 0 if self.version_number >= 0 else -1

        self.version_time = self.version_time or self.creation_time

        # Set the location to current if not located and not mission
        # (missions are not located)
        if not self.located and self.type != self.TYPE_MISSION:
            self.location_choice = self.LOCATION_SELECTED
            self.current_location_lat = 0
            self.current_location_lon = 0

        # Recreate the Point (just in case lat/lon has changed)
        _old_point = self.point
        self.point = self._get_point()
        self.timezone = self.get_timezone_from_coordinates()
        if _old_point != self.point:
            _last_location_update = self.user.last_location_update
            _report_upload_time = self.server_upload_time or timezone.now()
            if _last_location_update is None or (_last_location_update and _report_upload_time >= _last_location_update):
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
            if self.note:
                if _note_tags := self.get_tags_from_note(self.note):
                    self.tags.set(
                        set(
                            list(self.tags.values_list('name', flat=True))
                            + _note_tags
                        )
                    )

            # NOTE: setting it here and not setting the field.default
            # in order to avoid publishing on bulk_create
            self.published_at = timezone.now()

            # Set mobile_app (case legacy API)
            if not self.mobile_app and self.package_name and self.package_version:
                # NOTE: changing this will require a migration that matches the logic.
                self.mobile_app, _ = MobileApp.objects.get_or_create(
                    package_name=self.package_name,
                    package_version=str(
                        Version(
                            major=0,
                            minor=int(self.package_version),
                            patch=0,
                            build=('legacy',)
                        )
                    )
                )
            # Update device according to the information provided in the report.
            with transaction.atomic():
                # Try to find an existing device with model=self.device_model or fallback to the last model=None
                device = Device.objects.filter(
                    user=self.user,
                    model=self.device_model or '',
                ).select_for_update().order_by('-last_login').first() or Device.objects.filter(
                    user=self.user,
                    model__isnull=True,
                    active_session=True,
                    pk__in=models.Subquery(
                        Device.objects.filter(
                            user=models.OuterRef('user'),
                        ).order_by('-last_login').values('pk')[:1]
                    )
                ).select_for_update().first()

                if device:
                    # Handle registration_id transfer if an active, newer device exists
                    loggedin_active_devices_qs = Device.objects.filter(
                        user=self.user,
                        active=True,
                        model__isnull=True,
                        last_login__gt=device.last_login or timezone.now()
                    ).exclude(pk=device.pk)
                    if last_loggedin_active_device := loggedin_active_devices_qs.order_by('-last_login').first():
                        device.registration_id = last_loggedin_active_device.registration_id
                        Report.objects.filter(device__in=loggedin_active_devices_qs).update(
                            device=device
                        )
                        loggedin_active_devices_qs.delete()
                else:
                    # If still no device exists, create a new one
                    device = Device(user=self.user)

                # Update the device fields
                device.manufacturer = self.device_manufacturer
                device.model = self.device_model
                device.type = {
                    'android': 'android',
                    'ipados': 'ios',
                    'ios': 'ios',
                    'iphone os': 'ios',
                    '': None  # Mapping for empty or None value
                }.get(self.os.lower() if self.os else '')
                device.os_name = self.os
                device.os_version = self.os_version
                device.os_locale = self.os_language
                device.mobile_app = self.mobile_app
                device.active_session = True
                device.active = True
                device.last_login = timezone.now()

                device.save()

            self.device = device

        if self.tags.filter(name='345').exists():
            self.hide = True

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
                self.nuts_3_fk = self._get_nuts_is_in(levl_code=3)
                self.nuts_2_fk = self._get_nuts_is_in(levl_code=2)
            else:
                # Check if masked because of is in the ocean of out of the artic/antartic circle.
                self.location_is_masked = self.point.y > settings.MAX_ALLOWED_LATITUDE \
                    or self.point.y < settings.MIN_ALLOWED_LATITUDE \
                    or settings.OCEAN_GEOM.contains(self.point)
            self.lau_fk = LauEurope.objects.filter(geom__contains=self.point).first()

        self.nuts_3 = self.nuts_3_fk.nuts_id if self.nuts_3_fk else None
        self.nuts_2 = self.nuts_2_fk.nuts_id if self.nuts_2_fk else None

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

        if (self.type not in self.PUBLISHABLE_TYPES) or (not self.is_browsable) or (self.country and not self.country.reports_can_be_published):
            self.published_at = None

        super(Report, self).save(*args, **kwargs)

        self.user.update_score()

        if not self.is_browsable:
            _identification_task = getattr(self, "identification_task", None)
            if _identification_task:
                _identification_task.status = IdentificationTask.Status.ARCHIVED
                _identification_task.save()

        if self.type != self.TYPE_ADULT:
            IdentificationTask.objects.filter(report=self).delete()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.version_number = -1
        self.save_without_historical_record()

    def restore(self):
        self.deleted_at = None
        self.version_number = 0
        self.save_without_historical_record()

        _identification_task = getattr(self, "identification_task", None)
        if _identification_task:
            _identification_task.refresh(force=True)

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
            ),
            models.CheckConstraint(
                name='is_browsable_when_published',
                check=models.Q(published_at__isnull=True) |  # Allow if published_at is NULL
                    (
                        models.Q(hide=False) & models.Q(deleted_at__isnull=True) & models.Q(location_is_masked=False)
                    )
            )
        ]
        indexes = [
            # NOTE: Improve performance of api.v0.views.ReportViewSet
            models.Index(fields=["user", "type", "report_id"]),
            # NOTE: Improve performance of /api/observations when 
            # filtering by non_deleted() and published() endpoint.
            models.Index(
                fields=["published_at"],
                name="report_visible_published_idx",
                condition=Q(
                    deleted_at__isnull=True,
                    hide=False,
                    location_is_masked=False,
                    point__isnull=False,
                    published_at__isnull=False,
                ),
            ),
        ]

    def __unicode__(self):
        return self.pk

    def get_final_photo_url_for_notification(self):
        identification_task = getattr(self, "identification_task", None)
        photo = None
        if identification_task:
            photo = identification_task.photo
        elif self.n_visible_photos > 0:
            photo = self.get_first_visible_photo()

        return photo.get_medium_url() if photo else None

    def get_first_visible_photo(self):
        return self.visible_photos.first()

    def get_final_photo_html(self):
        identification_task = getattr(self, "identification_task", None)
        return identification_task.photo if identification_task else None


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
                report_obj.breeding_site_type = Report.BreedingSiteType.STORM_DRAIN
            elif self.answer_id == 122:
                report_obj.breeding_site_type = Report.BreedingSiteType.OTHER
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

    objects = PhotoManager()

    def __unicode__(self):
        return self.photo.name

    @property
    def user(self):
        return self.report.user

    @property
    def date(self):
        return self.report.version_time.strftime("%d-%m-%Y %H:%M")

    def get_small_path(self):
        return self.photo.path.replace('tigapics/', 'tigapics_small/')

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

    def save(self, *args, **kwargs):

        _is_adding = self._state.adding

        super().save(*args, **kwargs)

        if not _is_adding:
            return

        if self.report.type == Report.TYPE_ADULT:
            IdentificationTask.get_or_create_for_report(report=self.report)
        elif self.report.type == Report.TYPE_SITE:
            self.report.published_at = self.report.server_upload_time + timedelta(days=2)
            self.report.save()

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

    # TODO: replace masked_lon/masked_lat to Point (snaptogrid)
    @property
    def point(self):
        return Point(x=self.masked_lon, y=self.masked_lat, srid=4326)

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
        return result_local or result_en or ""

    def get_title(self, language_code: Optional[str] = None) -> str:
        return self._get_localized_field(fieldname_prefix='title', language_code=language_code)

    def get_body_html(self, language_code: Optional[str] = None) -> str:
        return self._get_localized_field(fieldname_prefix='body_html', language_code=language_code)

    def get_body(self, language_code: Optional[str] = None) -> str:
        body_html = self.get_body_html(language_code=language_code)
        soup = BeautifulSoup(body_html, 'html.parser')
        body = soup.find('body')  # Try to find the <body> tag
        if body:
            return body.get_text(separator=' ', strip=True)  # If <body> is found, extract text
        else:
            # If no <body> tag is found, return text from the entire HTML document
            return soup.get_text(separator=' ', strip=True)

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
                ),
                # NOTE: priority high is needed to show notification when the app is in foreground.
                # see https://firebase.google.com/docs/cloud-messaging/flutter/receive#foreground_and_notification_messages
                priority='high'
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


class OWCampaigns(models.Model):
    """
    This model contains the information about Overwintering campaigns. Each campaign takes place in a given country,
    over a period of time. In a given country at a given period, only one campaign can be active.
    """
    country = models.ForeignKey(EuropeCountry, related_name="campaigns", help_text='Country in which the campaign is taking place', on_delete=models.PROTECT, )
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

