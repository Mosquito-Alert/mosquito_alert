from typing import List, Optional
import uuid
import os

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db import transaction
from django.contrib.gis.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from langcodes import Language, closest_supported_match, standardize_tag as standarize_language_tag, tag_is_valid as language_tag_is_valid
from numpyencoder import NumpyEncoder
import pydenticon

from mosquito_alert.geo.models import EuropeCountry, NutsEurope

from .permissions import UserRolePermissionMixin, Role, AnnotationPermission, IdentificationTaskPermission, BasePermission

User = get_user_model()

class UserStat(UserRolePermissionMixin, models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, )
    grabbed_reports = models.IntegerField('Grabbed reports', default=0, help_text='Number of reports grabbed since implementation of simplified reports. For each 3 reports grabbed, one is simplified')
    national_supervisor_of = models.ForeignKey(EuropeCountry, blank=True, null=True, related_name="supervisors", help_text='Country of which the user is national supervisor. It means that the user will receive all the reports in his country', on_delete=models.PROTECT, )
    native_of = models.ForeignKey(EuropeCountry, blank=True, null=True, related_name="natives", help_text='Country in which the user operates. Used mainly for filtering purposes', on_delete=models.SET_NULL, )
    license_accepted = models.BooleanField('Value is true if user has accepted the license terms of EntoLab', default=False)

    nuts2_assignation = models.ForeignKey(NutsEurope, blank=True, null=True, related_name="nuts2_assigned", help_text='Nuts2 division in which the user operates. Influences the priority of report assignation', on_delete=models.SET_NULL, )

    def __str__(self):
        geo_label = ''
        if self.native_of:
            geo_label = self.native_of.name_engl
        if self.nuts2_assignation:
            geo_label += "{0} ({1})".format(self.nuts2_assignation.europecountry.name_engl, self.nuts2_assignation.name_latn)
        return f"{self.user.username} - {geo_label}"

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

    # TODO: delete this, no longer used
    @transaction.atomic
    def assign_reports(self, country: Optional[EuropeCountry] = None) -> List[Optional['identification_tasks.IdentificationTask']]:
        from mosquito_alert.identification_tasks.models import IdentificationTask

        task_queue = IdentificationTask.objects.exclude(assignees=self.user).select_related('report')
        if country is not None:
            task_queue = task_queue.filter(report__country=country)

        if self.is_superexpert():
            task_queue = task_queue.to_review().order_by('created_at')
        else:
            task_queue = task_queue.backlog(user=self.user)
            # Only assign until reaching the maximum allowed.
            current_pending = self.num_pending_annotations
            if current_pending >= settings.MAX_N_OF_PENDING_REPORTS:
                return

            num_to_assign = settings.MAX_N_OF_PENDING_REPORTS - current_pending
            task_queue = task_queue.all()[:num_to_assign]

        result = []
        for task in task_queue:
            task.assign_to_user(user=self.user)
            result.append(task)

        return result

    # NOTE: override UserRolePermissionMixin
    def get_countries_with_roles(self) -> List[EuropeCountry]:
        countries = []
        if country := self.native_of:
            countries.append(country)
        if country := self.national_supervisor_of:
            countries.append(country)
        return list(set(countries))

    # NOTE: override UserRolePermissionMixin
    def get_role(self, country: Optional[EuropeCountry] = None) -> Role:
        from mosquito_alert.identification_tasks.models import IdentificationTask

        if self.user.is_superuser:
            return Role.ADMIN
        if self.user.has_perm('%(app_label)s.add_review' % {
            'app_label': IdentificationTask._meta.app_label,
        }):
            return Role.REVIEWER
        if self.is_expert():
            if country and self.national_supervisor_of == country:
                return Role.SUPERVISOR
            return Role.ANNOTATOR
        return Role.BASE

    def _update_permissions_from_django_perms(self, perm_obj: BasePermission, model_class: models.Model):
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        perm_template = f"{app_label}.{{action}}_{model_name}"

        for action in ['add', 'view', 'change', 'delete']:
            if self.user.has_perm(perm_template.format(action=action)):
                setattr(perm_obj, action, True)
        return perm_obj

    # NOTE: override UserRolePermissionMixin
    def get_role_annotation_permission(self, role: Role) -> AnnotationPermission:
        from mosquito_alert.identification_tasks.models import ExpertReportAnnotation

        perm = super().get_role_annotation_permission(role=role)
        return self._update_permissions_from_django_perms(perm, ExpertReportAnnotation)

    # NOTE: override UserRolePermissionMixin
    def get_role_identification_task_permission(self, role: Role) -> IdentificationTaskPermission:
        from mosquito_alert.identification_tasks.models import IdentificationTask

        perm = super().get_role_identification_task_permission(role=role)
        return self._update_permissions_from_django_perms(perm, IdentificationTask)

    def is_expert(self):
        return self.user.groups.filter(name="expert").exists()

    def is_superexpert(self):
        return self.user.groups.filter(name="superexpert").exists()

    def is_bb_user(self):
        if self.native_of is not None:
            return self.native_of.is_bounding_box
        return False

    def is_national_supervisor(self):
        return self.national_supervisor_of is not None

    def is_national_supervisor_for_country(self, country):
        return self.is_national_supervisor() and self.national_supervisor_of.gid == country.gid
    
    @property
    def formatted_country_info(self):
        this_user = self.user
        this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
        this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
        this_user_is_europe = this_user.groups.filter(name='eu_group_europe').exists()
        this_user_is_spain = not this_user_is_europe
        if this_user_is_spain:
            if this_user_is_team_bcn:
                return "Spain - Barcelona"
            elif this_user_is_team_not_bcn:
                return "Spain - Outside Barcelona"
            else:
                return "Spain - Global"
        else:
            if self.is_national_supervisor():
                return "Europe - National supervisor - " + self.national_supervisor_of.name_engl
            elif country := self.native_of:
                return "Europe - " + country.name_engl
            else:
                return ""


    # this method returns the username, changing any '.' character to a '_'. This is used to avoid usernames used
    # as id or class names in views to break jquery selector queries
    @property
    def username_nopoint(self):
        return self.user.username.replace('.', '_')

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
        db_table = 'tigacrafting_userstat' # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.


def get_default_password_hash():
    return make_password(settings.DEFAULT_TIGAUSER_PASSWORD)

class TigaUser(UserRolePermissionMixin, AbstractBaseUser, AnonymousUser):
    AVAILABLE_LANGUAGES = [
        (standarize_language_tag(code), Language.get(code).autonym().title()) for code, _ in settings.LANGUAGES
    ]

    USERNAME_FIELD = 'pk'

    password = models.CharField(_('password'), max_length=128, default=get_default_password_hash)

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
        from mosquito_alert.tigaserver_app.models import Device
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
            generator = pydenticon.Generator(5, 5, foreground=[
                "rgb(45,79,255)",
                "rgb(254,180,44)",
                "rgb(226,121,234)",
                "rgb(30,179,253)",
                "rgb(232,77,65)",
                "rgb(49,203,115)",
                "rgb(141,69,170)"
            ])
            identicon_png = generator.generate(str(self.user_UUID), 200, 200, output_format="png")
            f = open(file_path, "wb")
            f.write(identicon_png)
            f.close()
        return settings.MEDIA_URL + "identicons/" + str(self.user_UUID) + ".png"

    def get_role(self, country: Optional[EuropeCountry] = None) -> Role:
        return Role.BASE

    def get_countries_with_roles(self) -> List[EuropeCountry]:
        return []

    def update_score(self, commit: bool = True) -> None:
        # NOTE: placing import here due to circular import
        from mosquito_alert.awards.xp_scoring import compute_user_score_in_xp_v2

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
        from mosquito_alert.notifications.models import NotificationTopic, UserSubscription
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
        db_table = 'tigaserver_app_tigauser' # NOTE: migrate from old tigacrafting, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
        verbose_name = "user"
        verbose_name_plural = "users"
