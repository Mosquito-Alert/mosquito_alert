from typing import Optional, TYPE_CHECKING
import uuid
import os

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from langcodes import (
    Language,
    closest_supported_match,
    standardize_tag as standarize_language_tag,
    tag_is_valid as language_tag_is_valid,
)
from numpyencoder import NumpyEncoder
import pydenticon

from mosquito_alert.geo.models import Country, NutsEurope

if TYPE_CHECKING:
    from mosquito_alert.devices.models import Device

User = get_user_model()


class UserStat(models.Model):
    user = models.OneToOneField(
        User,
        primary_key=True,
        on_delete=models.CASCADE,
    )
    country = models.ForeignKey(
        Country,
        blank=True,
        null=True,
        help_text="Country in which the user operates.",
        on_delete=models.SET_NULL,
    )
    license_accepted = models.BooleanField(
        "Value is true if user has accepted the license terms of EntoLab", default=False
    )

    nuts2_assignation = models.ForeignKey(
        NutsEurope,
        blank=True,
        null=True,
        related_name="nuts2_assigned",
        help_text="Nuts2 division in which the user operates. Influences the priority of report assignation",
        on_delete=models.SET_NULL,
    )

    @property
    def completed_annotations(self):
        return self.user.expert_report_annotations.filter(is_finished=True)

    @property
    def num_completed_annotations(self) -> int:
        return self.completed_annotations.count()

    @property
    def pending_annotations(self):
        return self.user.expert_report_annotations.filter(is_finished=False)

    @property
    def num_pending_annotations(self) -> int:
        return self.pending_annotations.count()

    # this method returns the username, changing any '.' character to a '_'. This is used to avoid usernames used
    # as id or class names in views to break jquery selector queries
    @property
    def username_nopoint(self):
        return self.user.username.replace(".", "_")

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserStat.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        try:
            instance.userstat.save()
        except UserStat.DoesNotExist:
            UserStat.objects.create(user=instance)

    class Meta:
        db_table = "tigacrafting_userstat"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.

    def __str__(self):
        return self.user.username


def get_default_password_hash():
    return make_password(settings.DEFAULT_TIGAUSER_PASSWORD)


class TigaUser(AbstractBaseUser, AnonymousUser):
    AVAILABLE_LANGUAGES = [
        (standarize_language_tag(code), Language.get(code).autonym().title())
        for code, _ in settings.LANGUAGES
    ]

    USERNAME_FIELD = "pk"

    password = models.CharField(
        _("password"), max_length=128, default=get_default_password_hash
    )

    user_UUID = models.CharField(
        max_length=36,
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="UUID randomly generated on "
        "phone to identify each unique user. Must be exactly 36 "
        "characters (32 hex digits plus 4 hyphens).",
    )
    registration_time = models.DateTimeField(
        auto_now_add=True,
        help_text="The date and time when user "
        "registered and consented to sharing "
        "data. Automatically set by "
        "server when user uploads registration.",
    )

    score = models.IntegerField(
        help_text="Score associated with user. This field is used only if the user does not have a profile",
        default=0,
    )

    score_v2 = models.IntegerField(
        help_text="Global XP Score. This field is updated whenever the user asks for the score, and is only stored here. The content must equal score_v2_adult + score_v2_bite + score_v2_site",
        default=0,
    )

    score_v2_adult = models.IntegerField(help_text="Adult reports XP Score.", default=0)

    score_v2_bite = models.IntegerField(help_text="Bite reports XP Score.", default=0)

    score_v2_site = models.IntegerField(help_text="Site reports XP Score.", default=0)

    # NOTE using NumpyEncoder since compute_user_score_in_xp_v2 function get result from pandas dataframe
    # and some integer are np.int64, which can not be encoded with the regular json library setup.
    score_v2_struct = models.JSONField(
        encoder=NumpyEncoder, help_text="Full cached score data", null=True, blank=True
    )

    last_score_update = models.DateTimeField(
        help_text="Last time score was updated", null=True, blank=True
    )

    last_location = models.PointField(null=True, blank=True, srid=4326)
    last_location_update = models.DateTimeField(
        help_text="Last time location was updated", null=True, blank=True
    )

    locale = models.CharField(
        choices=AVAILABLE_LANGUAGES,
        max_length=16,
        default="en",
        validators=[language_tag_is_valid],
        help_text="The locale code representing the language preference selected by the user for displaying the interface text. Enter the locale following the BCP 47 standard in 'language' or 'language-region' format (e.g., 'en' for English, 'en-US' for English (United States), 'fr' for French). The language is a two-letter ISO 639-1 code, and the region is an optional two-letter ISO 3166-1 alpha-2 code.",
    )

    @property
    def language_iso2(self) -> str:
        return Language.get(self.locale).language.lower()

    @property
    def last_device(self) -> Optional["Device"]:
        from mosquito_alert.devices.models import Device

        try:
            return self.devices.latest("date_created")
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
        return str(self.user_UUID)

    def __str__(self):
        return str(self.user_UUID)

    def get_user_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return set()

    def has_perm(self, perm, obj=None):
        return False

    def has_module_perms(self, module):
        return False

    def get_identicon(self):
        file_path = settings.MEDIA_ROOT + "/identicons/" + str(self.user_UUID) + ".png"
        if not os.path.exists(file_path):
            generator = pydenticon.Generator(
                5,
                5,
                foreground=[
                    "rgb(45,79,255)",
                    "rgb(254,180,44)",
                    "rgb(226,121,234)",
                    "rgb(30,179,253)",
                    "rgb(232,77,65)",
                    "rgb(49,203,115)",
                    "rgb(141,69,170)",
                ],
            )
            identicon_png = generator.generate(
                str(self.user_UUID), 200, 200, output_format="png"
            )
            f = open(file_path, "wb")
            f.write(identicon_png)
            f.close()
        return settings.MEDIA_URL + "identicons/" + str(self.user_UUID) + ".png"

    def update_score(self, commit: bool = True) -> None:
        # NOTE: placing import here due to circular import
        from mosquito_alert.awards.xp_scoring import compute_user_score_in_xp_v2

        score_dict = compute_user_score_in_xp_v2(user_uuid=self.pk)
        self.score_v2_struct = score_dict

        try:
            self.score_v2_adult = score_dict["score_detail"]["adult"]["score"]
        except (KeyError, TypeError):
            self.score_v2_adult = 0

        try:
            self.score_v2_bite = score_dict["score_detail"]["bite"]["score"]
        except (KeyError, TypeError):
            self.score_v2_bite = 0

        try:
            self.score_v2_site = score_dict["score_detail"]["site"]["score"]
        except (KeyError, TypeError):
            self.score_v2_site = 0

        self.score_v2 = sum(
            [self.score_v2_adult, self.score_v2_bite, self.score_v2_site]
        )
        self.last_score_update = timezone.now()

        if commit:
            self.save()

    def save(self, *args, **kwargs):

        if self.locale:
            self.locale = (
                closest_supported_match(
                    self.locale, [code for code, _ in self.AVAILABLE_LANGUAGES]
                )
                or "en"
            )

        result = super().save(*args, **kwargs)

        # Make sure user is subscribed to global topic
        from mosquito_alert.notifications.models import (
            NotificationTopic,
            UserSubscription,
        )

        try:
            global_topic = NotificationTopic.objects.get(topic_code="global")
        except NotificationTopic.DoesNotExist:
            pass
        else:
            UserSubscription.objects.get_or_create(user=self, topic=global_topic)

        # Subscribe user to the language selected.
        try:
            language_topic = NotificationTopic.objects.get(topic_code=self.locale)
        except NotificationTopic.DoesNotExist:
            pass
        else:
            UserSubscription.objects.get_or_create(user=self, topic=language_topic)

        return result

    class Meta:
        db_table = "tigaserver_app_tigauser"  # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
