
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from fcm_django.models import AbstractFCMDevice, DeviceType
from langcodes import standardize_tag as standarize_language_tag, tag_is_valid as language_tag_is_valid
from semantic_version import Version
from semantic_version.django_fields import VersionField
from simple_history.models import HistoricalRecords

from mosquito_alert.users.models import TigaUser

from .managers import DeviceManager


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
        db_table = 'tigaserver_app_mobileapp' # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
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
        table_name = 'tigaserver_app_historicaldevice', # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
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
        db_table = 'tigaserver_app_device' # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
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
