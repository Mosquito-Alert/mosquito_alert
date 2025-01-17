from typing import Optional, Literal

from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from taggit.managers import TaggableManager
from django.db.models.signals import post_save
from django.dispatch import receiver
import tigacrafting.html_utils as html_utils
import pytz

from .messages import other_insect_msg_dict, albopictus_msg_dict, albopictus_probably_msg_dict, culex_msg_dict, notsure_msg_dict

User = get_user_model()

def score_computation(n_total, n_yes, n_no, n_unknown = 0, n_undefined =0):
    return float(n_yes - n_no)/n_total


class CrowdcraftingTask(models.Model):
    task_id = models.IntegerField(unique=True, null=True, default=None)
    photo = models.OneToOneField('tigaserver_app.Photo', on_delete=models.PROTECT, )

    def __unicode__(self):
        return str(self.task_id)

    def get_mosquito_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined', mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score_cat(self):
        if self.get_tiger_validation_score() is not None:
            return int(round(2.499999 * self.get_tiger_validation_score(), 0))
        else:
            return None

    def get_site_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_site_validation_score_cat(self):
        if self.get_site_validation_score() is not None:
            return int(round(2.499999 * self.get_site_validation_score(), 0))
        else:
            return None

    def get_site_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, site_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_tiger_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no', tiger_question_response='undefined').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').exclude(user__user_id=None).count() + CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no', tiger_question_response='undefined').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_mosquito_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_crowdcrafting_n_responses(self):
        return CrowdcraftingResponse.objects.filter(task=self).count()

    mosquito_validation_score = property(get_mosquito_validation_score)
    tiger_validation_score = property(get_tiger_validation_score)
    site_validation_score = property(get_site_validation_score)
    site_individual_responses_html = property(get_site_individual_responses_html)
    tiger_individual_responses_html = property(get_tiger_individual_responses_html)
    mosquito_individual_responses_html = property(get_mosquito_individual_responses_html)
    crowdcrafting_n_responses = property(get_crowdcrafting_n_responses)
    tiger_validation_score_cat = property(get_tiger_validation_score_cat)
    site_validation_score_cat = property(get_site_validation_score_cat)


class CrowdcraftingUser(models.Model):
    user_id = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)


class CrowdcraftingResponse(models.Model):
    response_id = models.IntegerField()
    task = models.ForeignKey('tigacrafting.CrowdcraftingTask', related_name="responses", on_delete=models.CASCADE, )
    user = models.ForeignKey('tigacrafting.CrowdcraftingUser', related_name="responses", blank=True, null=True, on_delete=models.SET_NULL, )
    user_lang = models.CharField(max_length=10, blank=True)
    mosquito_question_response = models.CharField(max_length=100)
    tiger_question_response = models.CharField(max_length=100)
    site_question_response = models.CharField(max_length=100)
    created = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)


class Annotation(models.Model):
    user = models.ForeignKey('auth.User', related_name='annotations', on_delete=models.PROTECT, )
    task = models.ForeignKey('tigacrafting.CrowdcraftingTask', related_name='annotations', on_delete=models.CASCADE, )
    tiger_certainty_percent = models.IntegerField('Degree of belief',validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    value_changed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    working_on = models.BooleanField(default=False)

    def __unicode__(self):
        return "Annotation: " + str(self.id) + ", Task: " + str(self.task.task_id)


class MoveLabAnnotation(models.Model):
    task = models.OneToOneField(CrowdcraftingTask, related_name='movelab_annotation', on_delete=models.CASCADE, )
    CATEGORIES = ((-2, 'Definitely not a tiger mosquito'), (-1, 'Probably not a tiger mosquito'), (0, 'Not sure'), (1, 'Probably a tiger mosquito'), (2, 'Definitely a tiger mosquito'))
    tiger_certainty_category = models.IntegerField('Certainty', choices=CATEGORIES, blank=True, null=True)
    certainty_notes = models.TextField(blank=True)
    hide = models.BooleanField('Hide photo from public', default=False)
    edited_user_notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

TIGER_CATEGORIES = ((2, 'Definitely Aedes albopictus'), (1, 'Probably Aedes albopictus'),  (0, 'Not sure'), (-1, 'Probably neither albopictus nor aegypti'), (-2, 'Definitely not albopictus or aegypti'))

#WARNING!! THIS IS USED FOR VISUALIZATION ONLY, NEVER SHOULD BE USED FOR DATA INPUT!!!
TIGER_CATEGORIES_SEPARATED = ((2, 'Definitely Aedes albopictus'), (1, 'Probably Aedes albopictus'),  (0, 'Not sure'), (-1, 'Probably not albopictus'), (-2, 'Definitely not albopictus'))

AEGYPTI_CATEGORIES = ((2, 'Definitely Aedes aegypti'), (1, 'Probably Aedes aegypti'),  (0, 'Not sure'), (-1, 'Probably neither albopictus nor aegypti'), (-2, 'Definitely not albopictus or aegypti'))

#WARNING!! THIS IS USED FOR VISUALIZATION ONLY, NEVER SHOULD BE USED FOR DATA INPUT!!!
AEGYPTI_CATEGORIES_SEPARATED = ((2, 'Definitely Aedes aegypti'), (1, 'Probably Aedes aegypti'),  (0, 'Not sure'), (-1, 'Probably not aegypti'), (-2, 'Definitely not aegypti'))

SITE_CATEGORIES = ((2, 'Definitely a breeding site'), (1, 'Probably a breeding site'), (0, 'Not sure'), (-1, 'Probably not a breeding site'), (-2, 'Definitely not a breeding site'))

STATUS_CATEGORIES = ((1, 'public'), (0, 'flagged'), (-1, 'hidden'))

class ExpertReportAnnotation(models.Model):
    MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT = 3

    VALIDATION_CATEGORY_DEFINITELY = 2
    VALIDATION_CATEGORY_PROBABLY = 1

    VALIDATION_CATEGORIES = ((VALIDATION_CATEGORY_DEFINITELY, 'Definitely'), (VALIDATION_CATEGORY_PROBABLY, 'Probably'))

    user = models.ForeignKey(User, related_name="expert_report_annotations", on_delete=models.PROTECT, )
    report = models.ForeignKey('tigaserver_app.Report', related_name='expert_report_annotations', on_delete=models.CASCADE, )
    tiger_certainty_category = models.IntegerField('Tiger Certainty', choices=TIGER_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows a tiger mosquito')
    aegypti_certainty_category = models.IntegerField('Aegypti Certainty', choices=AEGYPTI_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows an Aedes aegypti')
    tiger_certainty_notes = models.TextField('Internal Species Certainty Comments', blank=True, help_text='Internal notes for yourself or other experts')
    site_certainty_category = models.IntegerField('Site Certainty', choices=SITE_CATEGORIES, default=None, blank=True, null=True, help_text='Your degree of belief that at least one photo shows a tiger mosquito breeding site')
    site_certainty_notes = models.TextField('Internal Site Certainty Comments', blank=True, help_text='Internal notes for yourself or other experts')
    edited_user_notes = models.TextField('Public Note', blank=True, help_text='Notes to display on public map')
    message_for_user = models.TextField('Message to User', blank=True, help_text='Message that user will receive when viewing report on phone')
    status = models.IntegerField('Status', choices=STATUS_CATEGORIES, default=1, help_text='Whether report should be displayed on public map, flagged for further checking before public display), or hidden.')
    #last_modified = models.DateTimeField(auto_now=True, default=datetime.now())
    last_modified = models.DateTimeField(default=timezone.now)
    validation_complete = models.BooleanField(default=False, help_text='Mark this when you have completed your review and are ready for your annotation to be displayed to public.')
    revise = models.BooleanField(default=False, help_text='For superexperts: Mark this if you want to substitute your annotation for the existing Expert annotations. Make sure to also complete your annotation form and then mark the "validation complete" box.')
    best_photo = models.ForeignKey('tigaserver_app.Photo', related_name='expert_report_annotations', null=True, blank=True, on_delete=models.SET_NULL, )
    linked_id = models.CharField('Linked ID', max_length=10, help_text='Use this field to add any other ID that you want to associate the record with (e.g., from some other database).', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    simplified_annotation = models.BooleanField(default=False, help_text='If True, the report annotation interface shows less input controls')
    tags = TaggableManager(blank=True)
    category = models.ForeignKey('tigacrafting.Categories', related_name='expert_report_annotations', null=True, blank=True, help_text='Simple category assigned by expert or superexpert. Mutually exclusive with complex. If this field has value, then probably there is a validation value', on_delete=models.SET_NULL, )
    complex = models.ForeignKey('tigacrafting.Complex', related_name='expert_report_annotations', null=True, blank=True, help_text='Complex category assigned by expert or superexpert. Mutually exclusive with category. If this field has value, there should not be a validation value', on_delete=models.SET_NULL, )
    validation_value = models.IntegerField('Validation Certainty', choices=VALIDATION_CATEGORIES, default=None, blank=True, null=True, help_text='Certainty value, 1 for probable, 2 for sure, 0 for none')
    other_species = models.ForeignKey('tigacrafting.OtherSpecies', related_name='expert_report_annotations', null=True, blank=True, help_text='Additional info supplied if the user selected the Other species category', on_delete=models.SET_NULL, )
    validation_complete_executive = models.BooleanField(default=False, help_text='Available only to national supervisor. Causes the report to be completely validated, with the final classification decided by the national supervisor')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'report'], name='unique_assignation')
        ]

    def is_superexpert(self):
        return self.user.groups.filter(name='superexpert').exists()

    def is_expert(self):
        return self.user.groups.filter(name='expert').exists()

    @property
    def is_on_ns_executive_validation_period(self):
        utc = pytz.UTC
        if self.report.country is not None:
            if UserStat.objects.filter(national_supervisor_of=self.report.country).exists():
                expiration_period = self.report.country.national_supervisor_report_expires_in
                if expiration_period is None:
                    expiration_period = 14
                date_now = datetime.now().replace(tzinfo=utc)
                date_expiration = date_now - timedelta(days=expiration_period)
                if self.report.server_upload_time >= date_expiration:
                    return True
        return False

    @classmethod
    def _get_auto_message(cls, category: 'Categories', validation_value: int, locale: str = 'en') -> Optional[str]:
        msg_dict = other_insect_msg_dict
        if not category:
            return msg_dict.get(locale)

        if category.pk == 4:  # albopictus
            msg_dict = albopictus_msg_dict if validation_value == cls.VALIDATION_CATEGORY_DEFINITELY else albopictus_probably_msg_dict
        elif category.pk == 10:  # culex
            msg_dict = culex_msg_dict
        elif category.pk == 9:  # not sure
            msg_dict = notsure_msg_dict

        return msg_dict.get(locale)

    @classmethod
    def create_auto_annotation(cls, report: 'tigaserver_app.models.Report', category: 'Categories', validation_value: Optional[Literal[VALIDATION_CATEGORY_PROBABLY, VALIDATION_CATEGORY_DEFINITELY]] = None):
        obj, _ = ExpertReportAnnotation.objects.update_or_create(
            user=User.objects.get(username="innie"),
            report=report,
            defaults={
                'validation_complete': True,
                'simplified_annotation': False,
                'best_photo': report.photos.first(),
                'category': category,
                'tiger_certainty_notes': 'auto',
                'validation_value': int(validation_value) if validation_value else None,
                'edited_user_notes': cls._get_auto_message(
                    category=category,
                    validation_value=int(validation_value) if validation_value else None,
                    locale=report.user.locale
                )
            }
        )
        obj.create_replicas()
        obj.create_super_expert_approval()

    def create_replicas(self):
        username_replicas = ["innie", "minnie", "manny"]

        report_annotations = ExpertReportAnnotation.objects.filter(report=self.report).count()
        if report_annotations >= self.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT:
            return
        num_missing_annotations = self.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - report_annotations

        fieldnames = [
            field.name for field in ExpertReportAnnotation._meta.fields if field.name not in ('id', 'user', 'report')
        ]
        obj_dict = {
            fname: getattr(self, fname) for fname in fieldnames
        }
        for dummy_user in User.objects.filter(username__in=username_replicas).exclude(username=self.user.username)[:num_missing_annotations]:
            ExpertReportAnnotation.objects.update_or_create(
                user=dummy_user,
                report=self.report,
                defaults={
                    **obj_dict,
                    'tiger_certainty_category': self.tiger_certainty_category,
                    'simplified_annotation': True,
                    'tiger_certainty_notes': 'exec_auto' if self.validation_complete_executive else 'auto',
                    'validation_complete': True,
                    'validation_complete_executive': False,
                    'best_photo': None,
                    'edited_user_notes': "",
                    'message_for_user': "",
                    'revise': False
                }
            )

    def create_super_expert_approval(self):
        ExpertReportAnnotation.objects.update_or_create(
            user=User.objects.get(username="super_reritja"),
            report=self.report,
            defaults={
                'status': 1,  # public
                'simplified_annotation': False,
                'revise': False,
                'validation_complete': True,
            }
        )

    # def get_photo_html_for_report_validation_wblood(self):
    #     #these_photos = Photo.objects.filter(report=self.report).visible()
    #     these_photos = self.report.photos.all()
    #     result = ''
    #     for photo in these_photos:
    #         male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
    #         female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
    #         fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
    #         #dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
    #         fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
    #         fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
    #         result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
    #                     '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
    #                 '</div>' \
    #                 '<br>' \
    #                 '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
    #                 '<br>' \
    #                '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
    #                '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
    #                '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="moon" aria-hidden="true"></i></label>' \
    #                '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="moon" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
    #                '</div>' \
    #
    #     return result

    def get_photo_html_for_report_validation_wblood(self):
        # these_photos = Photo.objects.filter(report=self.report).visible()
        these_photos = self.report.photos.all()
        result = ''
        for photo in these_photos:
            male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
            female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
            fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
            dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
            fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
            fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
            result += '<div class="rb_display_this_photo" data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                        '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
                    '</div>' \
                    '<br>' \
                    '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
                    '<br>' \
                   '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
                   '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="fa fa-dot-circle-o fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="fa fa-dot-circle-o fa-lg" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                   '<label title="Dont know" class="radio-inline"><input type="radio" value ="' + str(photo.id) + '_dk" name="fblood_' + str(photo.id) + '" ' + dk_status + '><i class="fa fa-question fa-lg" aria-hidden="true"></i></label>' \
                   '</div>'
        return result


    def get_photo_html_for_report_validation(self):
        #these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).visible()
        these_photos = self.report.photos.all()
        result = ''
        for photo in these_photos:
            result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                    '<input type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:' \
                    '</div>' \
                    '<br>' \
                    '<div style="border: 1px solid #333333;margin:1px;">' + photo.medium_image_for_validation_() + '</div>' \
                    '<br>'
        return result

    def get_photo_html_for_report_validation_superexpert(self):
        #these_photos = Photo.objects.filter(report__version_UUID=self.version_UUID).visible()
        these_photos = self.report.photos.all()
        result = ''

        for photo in these_photos:
            best_photo = ExpertReportAnnotation.objects.filter(best_photo=photo).exists()
            border_style = "3px solid green" if best_photo else "1px solid #333333"
            male_status = 'checked="checked"' if photo.blood_genre == 'male' else ''
            female_status = 'checked="checked"' if photo.blood_genre == 'female' else ''
            fblood_status = 'checked="checked"' if photo.blood_genre == 'fblood' else ''
            #dk_status = 'checked="checked"' if photo.blood_genre == 'dk' else ''
            fg_status = 'checked="checked"' if photo.blood_genre == 'fgravid' else ''
            fgb_status = 'checked="checked"' if photo.blood_genre == 'fgblood' else ''
            result += '<div data-ano-id="' + str(self.id) + '" id="div_for_photo_to_display_report_' + str(self.report.version_UUID) + '">' \
                        '<input data-best="' + str(best_photo) + '" type="radio" name="photo_to_display_report_' + str(self.report.version_UUID) + '" id="' + str(photo.id) + '" value="' + str(photo.id) + '"/>Display this photo on public map:'\
                        '</div>' \
                        '<br>' \
                        '<div style="border:' + border_style + ';margin:1px;position: relative;">' + photo.medium_image_for_validation_() + '</div>'
                        # '<div id="blood_status_' + str(self.report.version_UUID) + '_' + str(photo.id) + '">' \
                        # '<label title="Male" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_male" name="fblood_' + str(photo.id) + '" ' + male_status + '><i class="fa fa-mars fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_female" name="fblood_' + str(photo.id) + '" ' + female_status + '><i class="fa fa-venus fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female blood" class="radio-inline"><input value="' + str(photo.id) + '_fblood" type="radio" name="fblood_' + str(photo.id) + '" ' + fblood_status + '><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                        # '<label title="Female gravid" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgravid" name="fblood_' + str(photo.id) + '" ' + fg_status + '><i class="moon" aria-hidden="true"></i></label>' \
                        # '<label title="Female gravid + blood" class="radio-inline"><input type="radio" value="' + str(photo.id) + '_fgblood" name="fblood_' + str(photo.id) + '" ' + fgb_status + '><i class="moon" aria-hidden="true"></i><i class="fa fa-plus fa-lg" aria-hidden="true"></i><i class="fa fa-tint fa-lg" aria-hidden="true"></i></label>' \
                        # '</div>' \
                        # '<br>'
        return result

    def get_others_annotation_html(self):
        result = ''
        this_user = self.user
        this_report = self.report
        other_annotations = ExpertReportAnnotation.objects.filter(report=this_report).exclude(user=this_user)
        for ano in other_annotations.all():
            result += '<p>User: ' + ano.user.username + '</p>'
            result += '<p>Last Edited: ' + ano.last_modified.strftime("%d %b %Y %H:%m") + ' UTC</p>'
            if this_report.type == 'adult':
                result += '<p>Tiger Certainty: ' + (ano.get_tiger_certainty_category_display() if ano.get_tiger_certainty_category_display() else "") + '</p>'
                result += '<p>Tiger Notes: ' + ano.tiger_certainty_notes + '</p>'
            elif this_report.type == 'site':
                result += '<p>Site Certainty: ' + (ano.get_site_certainty_category_display() if ano.get_site_certainty_category_display() else "") + '</p>'
                result += '<p>Site Notes: ' + ano.site_certainty_notes + '</p>'
            result += '<p>Selected photo: ' + (ano.best_photo.popup_image() if ano.best_photo else "") + '</p>'
            result += '<p>Edited User Notes: ' + ano.edited_user_notes + '</p>'
            result += '<p>Message To User: ' + ano.message_for_user + '</p>'
            result += '<p>Status: ' + ano.get_status_display() if ano.get_status_display() else "" + '</p>'
            result += '<p>Validation Complete? ' + str(ano.validation_complete) + '</p><hr>'
        return result

    def get_score(self):
        score = -3
        if self.report.type == 'site':
            score = self.site_certainty_category
        elif self.report.type == 'adult':
            if self.aegypti_certainty_category == 2:
                score = 4
            elif self.aegypti_certainty_category == 1:
                score = 3
            else:
                score = self.tiger_certainty_category
        if score is not None:
            return score
        else:
            return -3

    def get_html_color_for_label(self):
        label = self.get_category_euro()
        return html_utils.get_html_color_for_label(label)

    def get_category_euro(self):
        if self.report.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_score()]
        elif self.report.type == 'adult':
            if self.category is None:
                # This should not happen, but safety first
                return "Unclassified"
            if self.category.specify_certainty_level:
                return dict(list(self.VALIDATION_CATEGORIES))[self.validation_value] + " " + self.category.name
            elif self.category.id == 8:
                return self.complex.description
            elif self.category.id == 2:
                if self.other_species:
                    return self.category.name + " - " + self.other_species.name
                else:
                    return self.category.name + " - not specified"
            else:
                return self.category.name

    def get_category(self):
        if self.report.type == 'site':
            return dict([(-3, 'Unclassified')] + list(SITE_CATEGORIES))[self.get_score()]
        elif self.report.type == 'adult':
            if self.get_score() > 2:
                return dict([(-3, 'Unclassified')] + list(AEGYPTI_CATEGORIES))[self.get_score()-2]
            else:
                return dict([(-3, 'Unclassified')] + list(TIGER_CATEGORIES))[self.get_score()]

    def get_status_bootstrap(self):
        result = '<span data-toggle="tooltip" data-placement="bottom" title="' + self.get_status_display() + '" class="' + ('glyphicon glyphicon-eye-open' if self.status == 1 else ('glyphicon glyphicon-flag' if self.status == 0 else 'glyphicon glyphicon-eye-close')) + '"></span>'
        return result

    def get_score_bootstrap(self):
        result = '<span class="label label-default" style="background-color:' + ('red' if self.get_score() == 2 else ('orange' if self.get_score() == 1 else ('white' if self.get_score() == 0 else ('grey' if self.get_score() == -1 else 'black')))) + ';">' + self.get_category() + '</span>'
        return result

    def _can_be_simplified(self) -> bool:
        # If the user is the superexpert -> False
        if self.user.userstat.is_superexpert():
            return False

        # If the user is the supervisor of that country -> False
        if self.user.userstat.national_supervisor_of:
            if self.user.userstat.national_supervisor_of == self.report.country:
                return False

        # Return False if no simplified_annotation found or if the objects to be
        # created is suposed to be the last.
        total_completed_annotations_qs = self.report.expert_report_annotations.all()
        return (
            total_completed_annotations_qs.filter(simplified_annotation=False).exists() or
            total_completed_annotations_qs.count() < self.MAX_N_OF_EXPERTS_ASSIGNED_PER_REPORT - 1
        )

    def save(self, *args, **kwargs):
        if not kwargs.pop('skip_lastmodified', False):
            self.last_modified = timezone.now()

        if self.category:
            self.tiger_certainty_category = -2
            if self.category.pk == 4: # albopictus
                self.tiger_certainty_category = 2

            self.aegypti_certainty_category = -2
            if self.category.pk == 5: # aegypti
                self.aegypti_certainty_category = 2

        # On create only
        if self._state.adding and not self.validation_complete:
            self.simplified_annotation = self._can_be_simplified()

        if self.simplified_annotation:
            self.message_for_user = ""
            self.best_photo = None

        super(ExpertReportAnnotation, self).save(*args, **kwargs)

        if self.validation_complete and self.validation_complete_executive:
            self.create_replicas()
            self.create_super_expert_approval()

    def delete(self, *args, **kwargs):
        if self.validation_complete_executive:
            ExpertReportAnnotation.objects.filter(
                report=self.report,
                validation_complete=True,
                validation_complete_executive=False
            ).filter(
                models.Q(user__username__in=["innie", "minnie"]) 
                | models.Q(user__username="super_reritja", revise=False)
            ).delete()

        return super().delete(*args, **kwargs)

class UserStat(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, )
    grabbed_reports = models.IntegerField('Grabbed reports', default=0, help_text='Number of reports grabbed since implementation of simplified reports. For each 3 reports grabbed, one is simplified')
    national_supervisor_of = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True, related_name="supervisors", help_text='Country of which the user is national supervisor. It means that the user will receive all the reports in his country', on_delete=models.PROTECT, )
    native_of = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True, related_name="natives", help_text='Country in which the user operates. Used mainly for filtering purposes', on_delete=models.SET_NULL, )
    license_accepted = models.BooleanField('Value is true if user has accepted the license terms of EntoLab', default=False)
    # When in crisis mode, several regional restrictions are disabled and the user preferently receives reports
    # from places where there has been a spike
    crisis_mode = models.BooleanField('Tells if the validator is working in crisis mode or not', default=False)
    last_emergency_mode_grab = models.ForeignKey('tigaserver_app.EuropeCountry', blank=True, null=True,related_name="emergency_pullers", help_text='Last country user pulled map data from', on_delete=models.SET_NULL, )
    nuts2_assignation = models.ForeignKey('tigaserver_app.NutsEurope', blank=True, null=True, related_name="nuts2_assigned", help_text='Nuts2 division in which the user operates. Influences the priority of report assignation', on_delete=models.SET_NULL, )

    def __str__(self):
        geo_label = ''
        if self.native_of:
            geo_label = self.native_of.name_engl
        if self.nuts2_assignation:
            geo_label += "{0} ({1})".format(self.nuts2_assignation.europecountry.name_engl, self.nuts2_assignation.name_latn)
        return f"{self.user.username} - {geo_label}"

    @property
    def completed_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=True)

    @property
    def num_completed_annotations(self) -> int:
        return self.completed_annotations.count()

    @property
    def pending_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=False)

    @property
    def num_pending_annotations(self) -> int:
        return self.pending_annotations.count()

    def has_accepted_license(self):
        return self.license_accepted

    def is_expert(self):
        return self.user.groups.filter(name="expert").exists()

    def is_superexpert(self):
        return self.user.groups.filter(name="superexpert").exists()

    def is_movelab(self):
        return self.user.groups.filter(name="movelab").exists()

    def is_team_bcn(self):
        return self.user.groups.filter(name="team_bcn").exists()

    def is_team_not_bcn(self):
        return self.user.groups.filter(name="team_not_bcn").exists()

    def is_team_everywhere(self):
        return self.user.groups.exclude(name="team_not_bcn").exclude(name="team_bcn").exists()

    def n_completed_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=True).count()

    def n_pending_annotations(self):
        return self.user.expert_report_annotations.filter(validation_complete=False).count()

    def is_bb_user(self):
        if self.native_of is not None:
            return self.native_of.is_bounding_box
        return False

    # only regular users can activate crisis mode
    def can_activate_crisis_mode(self):
        if self.is_superexpert():
            return False
        if self.is_bb_user():
            return False
        if self.is_national_supervisor():
            return False
        return True

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
        this_user_is_team_everywhere = self.is_team_everywhere()
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
            else:
                return "Europe - " + self.native_of.name_engl


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



class Categories(models.Model):
    name = models.TextField('Name of the classification category', help_text='Usually a species category. Can also be other/special case values')
    specify_certainty_level = models.BooleanField(default=False, help_text='Indicates if for this row a certainty level must be supplied')

    def __str__(self):
        return self.name


class Complex(models.Model):
    description = models.TextField('Name of the complex category', help_text='This table is reserved for species combinations')


class OtherSpecies(models.Model):
    name = models.TextField('Name of other species', help_text='List of other, not controlled species')
    category = models.TextField('Subcategory of other species', blank=True, help_text='The subcategory of other species, i.e. Other insects, Culicidae')
    ordering = models.IntegerField('Auxiliary help to tweak list ordering', blank=True, null=True)

    def __str__(self):
        return self.name


class FavoritedReports(models.Model):
    user = models.ForeignKey(User, related_name='favorited_by', help_text='User which marked the report as favorite', on_delete=models.CASCADE,)
    report = models.ForeignKey('tigaserver_app.Report', related_name='favorites', help_text='User which marked the report as favorite', on_delete=models.CASCADE)
    note = models.TextField('Brief note stating why this report interested you', blank=True, help_text='Add a brief description that will help you remember the report')

    class Meta:
        unique_together = ('user','report',)


class Alert(models.Model):
    xvb = models.BooleanField('Stands for expert validation based - if True, means that the alert was sent after expert validation. For False, it was sent before')
    report_id = models.CharField(help_text='Report related with the alert',max_length=40)
    report_datetime = models.DateTimeField()
    loc_code = models.CharField('Locale code - can be either a nuts3 code, or a nuts3_natcode (natcode is a municipality code) for spanish reports',max_length=25)
    cat_id = models.IntegerField('aima species category id')
    species = models.CharField('Species slug',max_length=25)
    certainty = models.FloatField('IA certainty value')
    status = models.CharField('Introduction status label',max_length=50, default='')
    hit = models.BooleanField('True if AIMA identification was initially correct, False if AIMA initially failed and was revised', blank=True, null=True)
    review_species = models.CharField('Revised species slug, can be empty', max_length=25, blank=True, null=True)
    review_status = models.CharField('Revised introduction status label', max_length=50, blank=True, null=True)
    review_datetime = models.DateTimeField('revision timestamp', blank=True, null=True )
    alert_sent = models.BooleanField('flag for alert sent or not yet', default=False)
    notes = models.TextField('Notes field for varied observations', blank=True, null=True)

# class Species(models.Model):
#     species_name = models.TextField('Scientific name of the objective species or combination of species', blank=True, help_text='This is the species latin name i.e Aedes albopictus')
#     composite = models.BooleanField(default=False, help_text='Indicates if this row is a single species or a combination')


# VALIDATION_CATEGORIES = ((2, 'Sure'), (1, 'Probably'), (0, 'None'))
# class Validation(models.Model):
#     report = models.ForeignKey('tigaserver_app.Report', related_name='report_speciesvalidations')
#     user = models.ForeignKey(User, related_name="user_speciesvalidations")
#     validation_time = models.DateTimeField(blank=True, null=True)
#     species = models.ForeignKey(Species, related_name='validations', blank=True, null=True)
#     #species = models.ManyToManyField(Species)
#     validation_value = models.IntegerField('Validation Certainty', choices=VALIDATION_CATEGORIES, default=None, blank=True, null=True, help_text='Certainty value, 1 for probable, 2 for sure')
