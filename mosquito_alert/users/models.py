from typing import List, Optional

from django.conf import settings
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

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